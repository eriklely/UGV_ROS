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

sudo apt install ros-humble-rviz-2d-overlay-plugins

sudo apt install ros-$ROS_DISTRO-rviz-satellite

## 2026-08-31
- **Issue identified**: GPS not showing in RViz - no connection between `base_link` and `gps` frame
- **Root cause**: Missing `navsat_transform_node` to convert GPS lat/lon (NavSatFix) to UTM coordinates in map/odom frame
- **Current state**: 
  - GPS driver (`nmea_navsat_driver`) publishes `NavSatFix` in `gps` frame (URDF has `gps` link with fixed joint to `base_link`)
  - EKF (`robot_localization`) only fuses odometry (`odom0: /odom_raw`) and IMU (`imu0: /imu/data`)
  - No GPS fusion in EKF config - missing `pose0` for GPS data
  - No `navsat_transform_node` to convert geographic → UTM coordinates
- **Fix needed**:
  1. Add `navsat_transform_node` to `gps.launch.py` to convert NavSatFix → Odometry in map frame
  2. Add GPS pose input (`pose0`) to EKF config (`ekf.yaml`) 
  3. Ensure frame IDs match: `navsat_transform` outputs to `odom` or `map`, EKF fuses it

---

## 2026-08-31
- **Issue identified**: GPS not showing in RViz - no connection between `base_link` and `gps` frame
- **Root cause**: Missing `navsat_transform_node` to convert GPS lat/lon (NavSatFix) to UTM coordinates in map/odom frame
- **Current state**: 
  - GPS driver (`nmea_navsat_driver`) publishes `NavSatFix` in `gps` frame (URDF has `gps` link with fixed joint to `base_link`)
  - EKF (`robot_localization`) only fuses odometry (`odom0: /odom_raw`) and IMU (`imu0: /imu/data`)
  - No GPS fusion in EKF config - missing `pose0` for GPS data
  - No `navsat_transform_node` to convert geographic → UTM coordinates
- **Fix needed**:
  1. Add `navsat_transform_node` to `gps.launch.py` to convert NavSatFix → Odometry in map frame
  2. Add GPS pose input (`pose0`) to EKF config (`ekf.yaml`) 
  3. Ensure frame IDs match: `navsat_transform` outputs to `odom` or `map`, EKF fuses it

### Fix Applied (2026-08-31)
- **Created** `src/ugv_main/ugv_bringup/param/navsat_transform.yaml` - navsat_transform_node config
- **Updated** `src/ugv_main/ugv_bringup/launch/gps.launch.py` - Added navsat_transform_node with proper remappings
- **Updated** `src/ugv_main/ugv_bringup/param/ekf.yaml`:
  - Added `map_frame: map` and changed `world_frame: map` (for GPS fusion)
  - Added `pose0: /gps/filtered` with position-only config (x, y only)
  - Added pose0 rejection thresholds for outlier filtering
- **Updated** `src/ugv_main/ugv_bringup/param/gps.yaml` - Added optional GPS quality parameters
- **Updated** `src/ugv_main/ugv_bringup/package.xml` - Added `robot_localization` exec_depend

### Expected Transform Chain After Fix:
```
map (world_frame) 
  └── odom (EKF output: odom->base_footprint)
        └── base_footprint
              └── base_link
                    └── gps (fixed joint, 0.1 0 0.2 offset)

navsat_transform_node:
  - Input: /gps/fix (NavSatFix in 'gps' frame) + /imu/data + /odom
  - Output: /gps/filtered (Odometry in 'map' frame)
  - Broadcasts: UTM -> map transform

EKF (world_frame: map):
  - odom0: /odom_raw (continuous, relative) → fuses x, y, yaw, vx, vyaw
  - imu0: /imu/data (yaw, vyaw)
  - pose0: /gps/filtered (absolute position) → fuses x, y only
```

---

*Log entries will be appended below as work progresses.*