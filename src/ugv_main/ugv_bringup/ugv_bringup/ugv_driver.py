#!/usr/bin/env python3
"""Legacy Waveshare command node.

Do not use this for motors, gimbal, or LEDs. Those commands go through
ugv_bringup, which already owns /dev/ttyAMA0.

This node is kept only so old launch files do not crash. If started, it
listens for low battery voltage and plays a warning sound. It never
opens the serial port.
"""
import os
import time
import subprocess

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


DEFAULT_WAV = '/home/ws/ugv_ws/src/ugv_main/ugv_bringup/ugv_bringup/low_battery.wav'


class UgvDriver(Node):
    def __init__(self, name):
        super().__init__(name)
        self.declare_parameter('voltage_warn_min', 0.1)
        self.declare_parameter('voltage_warn_max', 9.0)
        self.declare_parameter('voltage_warn_period', 5.0)
        self.declare_parameter('wav_path', DEFAULT_WAV)
        self.declare_parameter('aplay_device', 'plughw:3,0')

        self.voltage_warn_min = self.get_parameter('voltage_warn_min').value
        self.voltage_warn_max = self.get_parameter('voltage_warn_max').value
        self.voltage_warn_period = self.get_parameter('voltage_warn_period').value
        self.wav_path = self.get_parameter('wav_path').value
        self.aplay_device = self.get_parameter('aplay_device').value
        self._last_warn = 0.0

        self.create_subscription(Float32, 'voltage', self.voltage_callback, 10)

        self.get_logger().warn(
            'ugv_driver is a stub. cmd_vel, joint_commands and LED '
            'must be handled by ugv_bringup only. Serial port is not opened.'
        )

    def voltage_callback(self, msg):
        voltage_value = msg.data
        if not (self.voltage_warn_min < voltage_value < self.voltage_warn_max):
            return
        now = time.monotonic()
        if now - self._last_warn < self.voltage_warn_period:
            return
        self._last_warn = now
        self.get_logger().warn(f'Low battery: {voltage_value:.2f} V')
        if os.path.isfile(self.wav_path):
            subprocess.run(
                ['aplay', '-D', self.aplay_device, self.wav_path],
                check=False,
            )


def main(args=None):
    rclpy.init(args=args)
    node = UgvDriver('ugv_driver')
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()