#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rviz_2d_overlay_msgs.msg import OverlayText
from std_msgs.msg import Float32


class TemperatureOverlay(Node):
    def __init__(self):
        super().__init__('temperature_overlay')
        self.pub = self.create_publisher(OverlayText, '/rpi/temperature_overlay', 10)
        self.create_subscription(Float32, '/rpi/temperature', self.cb, 10)

    @staticmethod
    def _set_fg_color(overlay, temperature_c):
        if temperature_c >= 80.0:
            overlay.fg_color.r = 1.0
            overlay.fg_color.g = 0.0
            overlay.fg_color.b = 0.0
        elif temperature_c >= 70.0:
            overlay.fg_color.r = 1.0
            overlay.fg_color.g = 1.0
            overlay.fg_color.b = 0.0
        else:
            overlay.fg_color.r = 0.0
            overlay.fg_color.g = 1.0
            overlay.fg_color.b = 0.0
        overlay.fg_color.a = 1.0

    @classmethod
    def _build_overlay(cls, temperature_c):
        t = OverlayText()
        t.action = OverlayText.ADD
        t.width = 220
        t.height = 60
        t.horizontal_distance = 10
        t.vertical_distance = 80
        t.horizontal_alignment = OverlayText.RIGHT
        t.vertical_alignment = OverlayText.TOP
        t.text_size = 16.0
        cls._set_fg_color(t, temperature_c)
        t.bg_color.a = 0.4
        t.text = f'CPU Temp: {temperature_c:.1f} °C'
        return t

    def cb(self, msg):
        self.pub.publish(self._build_overlay(msg.data))


def main(args=None):
    rclpy.init(args=args)
    node = TemperatureOverlay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
