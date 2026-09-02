import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    ugv_nav = get_package_share_directory('ugv_nav')
    nav2 = get_package_share_directory('nav2_bringup')
    rviz_cfg = os.path.join(ugv_nav, 'rviz', 'view_nav_2d.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'map', default_value=os.path.join(ugv_nav, 'maps', 'map.yaml')),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(ugv_nav, 'param', 'amcl_teb.yaml')),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': LaunchConfiguration('map'),
                'params_file': LaunchConfiguration('params_file'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'slam': 'False',
                'use_composition': 'False',
                'autostart': 'true',
            }.items(),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_cfg],
            condition=IfCondition(LaunchConfiguration('use_rviz')),
        ),
    ])