#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from rviz_2d_overlay_msgs.msg import OverlayText

class VoltageOverlay(Node):
    def __init__(self):
        super().__init__('voltage_overlay')
        self.pub = self.create_publisher(OverlayText, '/voltage_overlay', 10)
        self.create_subscription(Float32, '/voltage', self.cb, 10)

    @staticmethod
    def _set_fg_color(overlay, voltage):
        if voltage > 11.0:
            overlay.fg_color.r = 0.0
            overlay.fg_color.g = 1.0
            overlay.fg_color.b = 0.0
        elif voltage >= 10.0:
            overlay.fg_color.r = 1.0
            overlay.fg_color.g = 0.5
            overlay.fg_color.b = 0.0
        else:
            overlay.fg_color.r = 1.0
            overlay.fg_color.g = 0.0
            overlay.fg_color.b = 0.0
        overlay.fg_color.a = 1.0

    def cb(self, msg):
        t = OverlayText()
        t.action = OverlayText.ADD
        t.width = 220
        t.height = 60
        t.horizontal_distance = 10
        t.vertical_distance = 10
        t.horizontal_alignment = OverlayText.LEFT
        t.vertical_alignment = OverlayText.TOP
        t.text_size = 16.0
        self._set_fg_color(t, msg.data)
        t.bg_color.a = 0.4
        t.text = f'Battery: {msg.data:.2f} V'
        self.pub.publish(t)

def main(args=None):
    rclpy.init(args=args)
    node = VoltageOverlay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()