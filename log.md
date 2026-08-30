# UGV_ROS Project Log

## 2026-08-30
- **Initial log creation** - Created log.md to track project progress and changes
- **Workspace structure**: ROS2 Humble workspace with `ugv_main/` (core packages) and `ugv_else/` (third-party packages)
- **Key packages in ugv_main**:
  - `ugv_base_node` - Base node implementation
  - `ugv_bringup` - Launch/bringup configurations
  - `ugv_chat_ai` - AI chat integration
  - `ugv_description` - URDF/robot description
  - `ugv_gazebo` - Gazebo simulation
  - `ugv_interface` - Actions/Services definitions
  - `ugv_nav` - Navigation stack
  - `ugv_slam` - SLAM functionality
  - `ugv_tools` - Utility tools
  - `ugv_vision` - Vision processing
  - `ugv_web_app` - Web interface
- **Key packages in ugv_else**:
  - `apriltag_ros` - AprilTag detection
  - `cartographer` - Cartographer SLAM
  - `costmap_converter` - Costmap conversion
  - `emcl2_ros2` - EMCL2 localization
  - `explore_lite` - Exploration
  - `gmapping` - Gmapping SLAM
  - `ldlidar` - LDLidar driver
  - `rf2o_laser_odometry` - Laser odometry
  - `robot_pose_publisher` - Pose publishing
  - `teb_local_planner` - TEB planner
  - `vizanti` - Visualization

---

Installed ros gps drivers
sudo apt install -y ros-humble-nmea-navsat-driver python3-serial
source /opt/ros/humble/setup.bash

ros2 run nmea_navsat_driver nmea_serial_driver --ros-args \
  -p port:=/dev/ttyUSB0 \
  -p baud:=38400 \
  -p frame_id:=gps \
  -r fix:=/gps/fix \
  -r vel:=/gps/vel \
  -r heading:=/gps/heading \
  -r time_reference:=/gps/time_reference

*Log entries will be appended below as work progresses.*