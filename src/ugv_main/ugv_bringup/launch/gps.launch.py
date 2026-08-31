import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    gps_params = os.path.join(
        get_package_share_directory('ugv_bringup'),
        'param',
        'gps.yaml',
    )
    
    navsat_params = os.path.join(
        get_package_share_directory('ugv_bringup'),
        'param',
        'navsat_transform.yaml',
    )

    return LaunchDescription([
        # GPS driver - publishes NavSatFix in 'gps' frame
        Node(
            package='nmea_navsat_driver',
            executable='nmea_serial_driver',
            name='nmea_serial_driver',
            namespace='gps',
            output='screen',
            parameters=[gps_params],
        ),
        
        # navsat_transform_node - converts NavSatFix (lat/lon) to Odometry in map/odom frame
        Node(
            package='robot_localization',
            executable='navsat_transform_node',
            name='navsat_transform',
            output='screen',
            parameters=[navsat_params],
            remappings=[
                ('gps/fix', '/gps/fix'),
                ('imu', '/imu/data'),
                ('odometry/filtered', '/odom'),
            ],
        ),
    ])