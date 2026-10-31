"""MoveIt move_group + RViz for the independent tabletop simulation."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    package_name = 'piper_tabletop_sim'
    package_share = get_package_share_directory(package_name)
    start_rviz = LaunchConfiguration('start_rviz')

    moveit_config = (
        MoveItConfigsBuilder('piper', package_name=package_name)
        .robot_description(file_path='config/piper.urdf.xacro')
        .robot_description_semantic(file_path='config/piper.srdf')
        .robot_description_kinematics(file_path='config/kinematics.yaml')
        .joint_limits(file_path='config/joint_limits.yaml')
        .trajectory_execution(
            file_path='config/moveit_controllers.yaml',
            moveit_manage_controllers=False,
        )
        .planning_pipelines(default_planning_pipeline='ompl', pipelines=['ompl'])
        .planning_scene_monitor(
            publish_planning_scene=True,
            publish_geometry_updates=True,
            publish_state_updates=True,
            publish_transforms_updates=True,
            publish_robot_description=True,
            publish_robot_description_semantic=True,
        )
        .to_moveit_configs()
    )

    move_group = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            moveit_config.to_dict(),
            {
                'use_sim_time': True,
                'allow_trajectory_execution': True,
                'moveit_manage_controllers': False,
                'trajectory_execution.allowed_start_tolerance': 0.05,
                'trajectory_execution.allowed_execution_duration_scaling': 3.0,
                'trajectory_execution.allowed_goal_duration_margin': 2.0,
            },
        ],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='piper_tabletop_rviz',
        output='screen',
        condition=IfCondition(start_rviz),
        arguments=['-d', os.path.join(package_share, 'config', 'moveit.rviz')],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            {'use_sim_time': True},
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('start_rviz', default_value='true'),
        move_group,
        rviz,
    ])
