"""ROS 2 publisher for Raspberry Pi CPU temperature."""

import re
import subprocess
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Float32


class RpiTemperaturePublisher(Node):
    """Publish Raspberry Pi temperature telemetry."""

    def __init__(self):
        super().__init__('rpi_temperature')
        self.declare_parameter('publish_rate_hz', 1.0)
        self.declare_parameter('warn_threshold_c', 70.0)
        self.declare_parameter('critical_threshold_c', 80.0)

        publish_rate_hz = self.get_parameter('publish_rate_hz').value
        if publish_rate_hz <= 0.0:
            self.get_logger().warning(
                'publish_rate_hz must be positive; using 1.0 Hz instead.'
            )
            publish_rate_hz = 1.0

        self._float_publisher = self.create_publisher(
            Float32,
            '/rpi/temperature',
            10,
        )
        self._temperature_publisher = self.create_publisher(
            Temperature,
            '/rpi/temperature_sensor',
            10,
        )
        self._timer = self.create_timer(
            1.0 / publish_rate_hz,
            self.publish_temperature,
        )
        self._read_error_logged = False
        self._last_warn_log_time = 0.0
        self._last_critical_log_time = 0.0
        self._threshold_log_period_s = 30.0

    @staticmethod
    def _parse_vcgencmd_output(output):
        """Parse vcgencmd output into a Celsius value."""

        match = re.search(r"temp=([0-9]+(?:\.[0-9]+)?)'C", output)
        if match is None:
            raise ValueError(f'Unexpected vcgencmd output: {output!r}')
        return float(match.group(1))

    def _read_sysfs_temperature(self):
        """Read the CPU temperature from the Linux thermal sysfs entry."""

        with open(
            '/sys/class/thermal/thermal_zone0/temp',
            'r',
            encoding='utf-8',
        ) as temp_file:
            return float(temp_file.read().strip()) / 1000.0

    def _read_vcgencmd_temperature(self):
        """Read the CPU temperature using vcgencmd."""

        result = subprocess.run(
            ['vcgencmd', 'measure_temp'],
            capture_output=True,
            text=True,
            check=True,
            timeout=2.0,
        )
        return self._parse_vcgencmd_output(result.stdout.strip())

    def _read_temperature_c(self):
        """Read temperature in Celsius with sysfs-first fallback behavior."""

        try:
            return self._read_sysfs_temperature()
        except Exception:
            return self._read_vcgencmd_temperature()

    def _log_read_failure(self, exc):
        """Log a read failure once until the next successful temperature read."""

        if not self._read_error_logged:
            self.get_logger().warning(
                f'Failed to read Raspberry Pi temperature: {exc}'
            )
            self._read_error_logged = True

    def _log_thresholds(self, temperature_c):
        """Log rate-limited temperature threshold warnings."""

        warn_threshold_c = self.get_parameter('warn_threshold_c').value
        critical_threshold_c = self.get_parameter('critical_threshold_c').value
        now = time.monotonic()

        if temperature_c >= critical_threshold_c:
            if now - self._last_critical_log_time >= self._threshold_log_period_s:
                self.get_logger().error(
                    f'Raspberry Pi CPU temperature critical: {temperature_c:.1f} °C'
                )
                self._last_critical_log_time = now
                self._last_warn_log_time = now
            return

        if temperature_c >= warn_threshold_c:
            if now - self._last_warn_log_time >= self._threshold_log_period_s:
                self.get_logger().warning(
                    f'Raspberry Pi CPU temperature high: {temperature_c:.1f} °C'
                )
                self._last_warn_log_time = now

    def publish_temperature(self):
        """Read and publish the current temperature."""

        try:
            temperature_c = self._read_temperature_c()
        except Exception as exc:
            self._log_read_failure(exc)
            return

        self._read_error_logged = False
        self._log_thresholds(temperature_c)

        float_msg = Float32()
        float_msg.data = temperature_c
        self._float_publisher.publish(float_msg)

        temperature_msg = Temperature()
        temperature_msg.header.stamp = self.get_clock().now().to_msg()
        temperature_msg.header.frame_id = 'rpi_cpu'
        temperature_msg.temperature = temperature_c
        self._temperature_publisher.publish(temperature_msg)


def main(args=None):
    """Run the Raspberry Pi temperature publisher node."""

    rclpy.init(args=args)
    node = RpiTemperaturePublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
