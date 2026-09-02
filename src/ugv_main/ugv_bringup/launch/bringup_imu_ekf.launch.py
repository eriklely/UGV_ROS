from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pub_odom_tf_arg = DeclareLaunchArgument(
        'pub_odom_tf', default_value='false',
        description='Wheels must not publish odom TF; local EKF owns it',
    )
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='false',
        description='Whether to launch RViz2',
    )
    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config', default_value='bringup',
        description='Choose which rviz configuration to use',
    )

    imu_filter_config = os.path.join(
        get_package_share_directory('ugv_bringup'),
        'param',
        'imu_filter_param.yaml',
    )

    driver_node = Node(
        package='ugv_bringup',
        executable='ugv_driver',
    )
    voltage_overlay_node = Node(
        package='ugv_bringup',
        executable='voltage_overlay',
        output='screen',
    )
    rpi_temperature_node = Node(
        package='ugv_bringup',
        executable='rpi_temperature',
        output='screen',
    )
    temperature_overlay_node = Node(
        package='ugv_bringup',
        executable='temperature_overlay',
        output='screen',
    )
    robot_state_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ugv_description'),
                'launch',
                'display.launch.py',
            )
        ),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': LaunchConfiguration('rviz_config'),
        }.items(),
    )
    imu_complementary_filter_node = Node(
        package='imu_complementary_filter',
        executable='complementary_filter_node',
        name='complementary_filter_gain_node',
        output='screen',
        parameters=[
            {'do_bias_estimation': True},
            {'do_adaptive_gain': True},
            {'use_mag': False},
            {'gain_acc': 0.01},
            {'gain_mag': 0.01},
        ],
    )
    laser_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ldlidar'),
                'launch',
                'ldlidar.launch.py',
            )
        )
    )
    rf2o_laser_odometry_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rf2o_laser_odometry'),
                'launch',
                'rf2o_laser_odometry.launch.py',
            )
        )
    )
    gps_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ugv_bringup'),
                'launch',
                'gps.launch.py',
            )
        )
    )
    base_node = Node(
        package='ugv_base_node',
        executable='base_node_ekf',
        parameters=[{'pub_odom_tf': LaunchConfiguration('pub_odom_tf')}],
    )
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(
            get_package_share_directory('ugv_bringup'), 'param', 'ekf.yaml')],
        remappings=[('/odometry/filtered', '/odom')],
    )
    ekf_map_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_map',
        output='screen',
        parameters=[os.path.join(
            get_package_share_directory('ugv_bringup'), 'param', 'ekf_gps.yaml')],
        remappings=[('/odometry/filtered', '/odometry/filtered_map')],
    )

    return LaunchDescription([
        pub_odom_tf_arg,
        use_rviz_arg,
        rviz_config_arg,
        robot_state_launch,
        driver_node,
        imu_complementary_filter_node,
        gps_bringup_launch,
        laser_bringup_launch,
        rf2o_laser_odometry_launch,
        voltage_overlay_node,
        rpi_temperature_node,
        temperature_overlay_node,
        base_node,
        ekf_node,
        ekf_map_node,
    ])