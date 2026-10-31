"""Bring up Gazebo + controllers + MoveIt + RViz."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg = get_package_share_directory('piper_tabletop_sim')
    sim_launch = os.path.join(pkg, 'launch', 'sim.launch.py')
    move_group_launch = os.path.join(pkg, 'launch', 'move_group.launch.py')

    gazebo_gui = LaunchConfiguration('gazebo_gui')
    camera_pitch_offset = LaunchConfiguration('camera_pitch_offset')
    start_rviz = LaunchConfiguration('start_rviz')

    return LaunchDescription([
        DeclareLaunchArgument('gazebo_gui', default_value='true'),
        DeclareLaunchArgument('camera_pitch_offset', default_value='1.047197551'),
        DeclareLaunchArgument('start_rviz', default_value='true'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sim_launch),
            launch_arguments={
                'gazebo_gui': gazebo_gui,
                'camera_pitch_offset': camera_pitch_offset,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(move_group_launch),
            launch_arguments={'start_rviz': start_rviz}.items(),
        ),
    ])
