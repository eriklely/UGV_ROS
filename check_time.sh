for n in /base_node /cartographer_node /cartographer_occupancy_grid_node /game_controller /ugv/joint_state_publisher /joy_ctrl /rf2o_laser_odometry /robot_pose_publisher /ugv/robot_state_publisher /rpi_temperature /rviz2 /temperature_overlay /ugv_driver /voltage_overlay; do
  echo -n "$n  "
  ros2 param get "$n" use_sim_time
done
