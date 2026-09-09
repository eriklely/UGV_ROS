#!/bin/bash
set -e

# Source ROS 2 and your workspace (adjust distro/path)
source ~/.bashrc

echo "Starting ugv_driver..."
ros2 run ugv_bringup ugv_driver &
sleep 1
echo "ugv_bringup ugv_driver started"

echo "Starting usb_cam..."
ros2 run usb_cam usb_cam_node_exe &
sleep 1
echo "usb_cam usb_cam_node_exe started"

echo "Starting apriltag_track_0..."
ros2 run ugv_vision apriltag_track_0 &
sleep 1
echo "ugv_vision apriltag_track_0 started"

echo "All nodes started. Press Ctrl+C to stop."
wait
