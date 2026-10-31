"""Gazebo Harmonic tabletop scene: one PiPER arm + D435i + table + 4 cm block."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg = get_package_share_directory('piper_tabletop_sim')
    xacro_file = os.path.join(pkg, 'urdf', 'piper_tabletop.urdf.xacro')
    world_file = os.path.join(pkg, 'worlds', 'tabletop.sdf')

    gazebo_gui = LaunchConfiguration('gazebo_gui')
    camera_pitch_offset = LaunchConfiguration('camera_pitch_offset')
    camera_update_rate = LaunchConfiguration('camera_update_rate')
    legacy_camera_topics = LaunchConfiguration('legacy_camera_topics')
    bridge_point_cloud = LaunchConfiguration('bridge_point_cloud')

    robot_description = ParameterValue(
        Command([
            'xacro ', xacro_file,
            ' camera_pitch_offset:=', camera_pitch_offset,
            ' camera_update_rate:=', camera_update_rate,
        ]),
        value_type=str,
    )

    # sdformat rewrites package://piper_tabletop_sim to model:// URLs. The
    # package parent must be on the Gazebo resource path as well as the package
    # directory itself.
    resource_path = os.pathsep.join(
        [os.path.dirname(pkg), pkg]
        + ([os.environ['GZ_SIM_RESOURCE_PATH']]
           if os.environ.get('GZ_SIM_RESOURCE_PATH') else [])
    )
    gz_env = {'GZ_SIM_RESOURCE_PATH': resource_path}

    gz_gui = ExecuteProcess(
        cmd=[
            'gz', 'sim', '-r', '-v', '3',
            '--physics-engine', 'gz-physics-bullet-featherstone-plugin',
            world_file,
        ],
        additional_env=gz_env,
        condition=IfCondition(gazebo_gui),
        output='screen',
    )
    gz_headless = ExecuteProcess(
        cmd=[
            'gz', 'sim', '-r', '-s', '--headless-rendering', '-v', '3',
            '--physics-engine', 'gz-physics-bullet-featherstone-plugin',
            world_file,
        ],
        additional_env=gz_env,
        condition=UnlessCondition(gazebo_gui),
        output='screen',
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )

    # RGBD output from the Gazebo sensor. The sensor publishes:
    #   /camera/depth/image          RGB
    #   /camera/depth/depth_image    depth
    #   /camera/depth/camera_info    intrinsics
    # Legacy ROS names are optional; the grasp pipeline uses the aliases below.
    camera_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='d435i_bridge',
        arguments=[
            '/camera/depth/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        condition=IfCondition(legacy_camera_topics),
        remappings=[
            ('/camera/depth/image', '/camera/color/image_raw'),
            ('/camera/depth/depth_image', '/camera/depth/image_raw'),
        ],
        output='screen',
    )

    # The RGBD sensor has one CameraInfo. Publish it under both the color and
    # depth names; the simulated RGB and depth are pixel-aligned.
    camera_color_info_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='d435i_color_info_bridge',
        arguments=[
            '/camera/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/camera/depth/camera_info', '/camera/color/camera_info'),
        ],
        condition=IfCondition(legacy_camera_topics),
        output='screen',
    )

    point_cloud_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='d435i_point_cloud_bridge',
        arguments=[
            '/camera/depth/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
        ],
        condition=IfCondition(bridge_point_cloud),
        output='screen',
    )

    # Aliases matching the real YOLO/GraspNet bridge defaults. The simulation
    # provides pixel-aligned RGB and depth, so the depth image is a valid
    # "aligned_depth_to_color" image.
    camera_alias_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='d435i_alias_bridge',
        arguments=[
            '/camera/depth/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/camera/depth/image', '/camera/camera/color/image_raw'),
            ('/camera/depth/depth_image',
             '/camera/camera/aligned_depth_to_color/image_raw'),
            ('/camera/depth/camera_info', '/camera/camera/color/camera_info'),
        ],
        output='screen',
    )

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
        output='screen',
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'piper_tabletop'],
        output='screen',
    )

    def spawner(name):
        return Node(
            package='controller_manager',
            executable='spawner',
            arguments=[
                name,
                '--controller-manager', '/controller_manager',
                '--controller-manager-timeout', '30',
                '--switch-timeout', '30',
            ],
            output='screen',
        )

    joint_state_broadcaster = spawner('joint_state_broadcaster')
    arm_controller = spawner('arm_controller')
    gripper_controller = spawner('gripper_controller')

    return LaunchDescription([
        DeclareLaunchArgument(
            'gazebo_gui', default_value='true',
            description='true = Gazebo GUI; false = headless server'),
        DeclareLaunchArgument(
            'camera_pitch_offset', default_value='1.047197551',
            description='D435i downward pitch in rad (60 deg). Set 0.0 for '
                        'the exact horizontal AG-robot camera attitude.'),
        DeclareLaunchArgument(
            'camera_update_rate', default_value='10.0',
            description='Simulated RGB-D frames per second.'),
        DeclareLaunchArgument(
            'legacy_camera_topics', default_value='false',
            description='Bridge extra legacy /camera/color and /camera/depth topics.'),
        DeclareLaunchArgument(
            'bridge_point_cloud', default_value='false',
            description='Bridge the optional RGB-D point cloud into ROS.'),

        gz_gui,
        gz_headless,
        clock_bridge,
        camera_bridge,
        camera_color_info_bridge,
        point_cloud_bridge,
        camera_alias_bridge,
        rsp,
        spawn,

        # The first seconds after spawn are the slowest (mesh loading +
        # rendering). Start controllers after that, then in sequence.
        RegisterEventHandler(OnProcessExit(
            target_action=spawn,
            on_exit=[TimerAction(period=4.0, actions=[joint_state_broadcaster])],
        )),
        RegisterEventHandler(OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[arm_controller],
        )),
        RegisterEventHandler(OnProcessExit(
            target_action=arm_controller,
            on_exit=[gripper_controller],
        )),
    ])
