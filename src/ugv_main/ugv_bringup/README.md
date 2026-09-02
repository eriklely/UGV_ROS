# ugv_bringup

## Raspberry Pi temperature topics

The basic bringup launch files now start an `rpi_temperature` node by default.
It publishes:

- `/rpi/temperature` as `std_msgs/msg/Float32` in °C
- `/rpi/temperature_sensor` as `sensor_msgs/msg/Temperature`
- `/rpi/temperature_overlay` as `rviz_2d_overlay_msgs/msg/OverlayText`

The `sensor_msgs/msg/Temperature` message uses
`header.frame_id = "rpi_cpu"` and sets `temperature` to the current CPU/SoC
reading.

### Parameters

- `publish_rate_hz` (default: `1.0`)
- `warn_threshold_c` (default: `70.0`)
- `critical_threshold_c` (default: `80.0`)

### Usage

```bash
ros2 topic echo /rpi/temperature
```

The node reads `/sys/class/thermal/thermal_zone0/temp` first and falls back to
`vcgencmd measure_temp`. It is intended for Raspberry Pi 4B systems running
Linux. On non-Pi systems the sysfs path may not exist; the node will log
warnings and keep running.

To view the temperature in RViz2, add an `OverlayText` display from
`rviz_2d_overlay_plugins` (**Add → By display type → OverlayText**) and set
its topic to `/rpi/temperature_overlay`. The raw numeric CPU temperature
remains available on `/rpi/temperature` as `std_msgs/msg/Float32`.
