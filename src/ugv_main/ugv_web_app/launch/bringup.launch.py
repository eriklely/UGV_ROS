import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    host_arg = DeclareLaunchArgument(
        'host',
        default_value='0.0.0.0',
        description='Address the Vizanti Flask server binds to'
    )

    vizanti_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('vizanti_server'),
                'launch',
                'vizanti_server.launch.py'
            )
        ),
        launch_arguments={
            'host': LaunchConfiguration('host'),
        }.items()
    )

    return LaunchDescription([
        host_arg,
        vizanti_launch
    ])