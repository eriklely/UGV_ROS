from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use /clock if true (Gazebo only)',
        ),
        Node(
            package='robot_pose_publisher',
            executable='robot_pose_publisher',
            name='robot_pose_publisher',
            output='screen',
            emulate_tty=True,
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'is_stamped': True,
                'map_frame': 'map',
                'base_frame': 'base_link',
            }],
        ),
    ])