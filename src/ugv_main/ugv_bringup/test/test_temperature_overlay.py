"""Unit tests for the temperature overlay helper."""

import sys
import types
import unittest


if 'rclpy' not in sys.modules:
    rclpy_module = types.ModuleType('rclpy')
    rclpy_node_module = types.ModuleType('rclpy.node')

    class DummyNode:
        pass

    rclpy_node_module.Node = DummyNode
    rclpy_module.node = rclpy_node_module
    sys.modules['rclpy'] = rclpy_module
    sys.modules['rclpy.node'] = rclpy_node_module

if 'std_msgs.msg' not in sys.modules:
    std_msgs_module = types.ModuleType('std_msgs')
    std_msgs_msg_module = types.ModuleType('std_msgs.msg')
    std_msgs_msg_module.Float32 = type('Float32', (), {})
    std_msgs_module.msg = std_msgs_msg_module
    sys.modules['std_msgs'] = std_msgs_module
    sys.modules['std_msgs.msg'] = std_msgs_msg_module

if 'rviz_2d_overlay_msgs.msg' not in sys.modules:
    rviz_module = types.ModuleType('rviz_2d_overlay_msgs')
    rviz_msg_module = types.ModuleType('rviz_2d_overlay_msgs.msg')

    class Color:
        def __init__(self):
            self.r = 0.0
            self.g = 0.0
            self.b = 0.0
            self.a = 0.0

    class OverlayText:
        ADD = 0
        LEFT = 0
        TOP = 0

        def __init__(self):
            self.action = None
            self.width = 0
            self.height = 0
            self.horizontal_distance = 0
            self.vertical_distance = 0
            self.horizontal_alignment = None
            self.vertical_alignment = None
            self.text_size = 0.0
            self.fg_color = Color()
            self.bg_color = Color()
            self.text = ''

    rviz_msg_module.OverlayText = OverlayText
    rviz_module.msg = rviz_msg_module
    sys.modules['rviz_2d_overlay_msgs'] = rviz_module
    sys.modules['rviz_2d_overlay_msgs.msg'] = rviz_msg_module

from ugv_bringup.temperature_overlay import TemperatureOverlay


class TemperatureOverlayTests(unittest.TestCase):
    def test_build_overlay_formats_text_and_layout(self):
        overlay = TemperatureOverlay._build_overlay(47.34)

        self.assertEqual(overlay.text, 'CPU Temp: 47.3 °C')
        self.assertEqual(overlay.width, 220)
        self.assertEqual(overlay.height, 60)
        self.assertEqual(overlay.horizontal_distance, 10)
        self.assertEqual(overlay.vertical_distance, 80)
        self.assertEqual(overlay.text_size, 16.0)
        self.assertEqual(overlay.bg_color.a, 0.4)

    def test_build_overlay_uses_green_below_warn_threshold(self):
        overlay = TemperatureOverlay._build_overlay(69.9)

        self.assertEqual((overlay.fg_color.r, overlay.fg_color.g, overlay.fg_color.b), (0.0, 1.0, 0.0))

    def test_build_overlay_uses_yellow_at_warn_threshold(self):
        overlay = TemperatureOverlay._build_overlay(70.0)

        self.assertEqual((overlay.fg_color.r, overlay.fg_color.g, overlay.fg_color.b), (1.0, 1.0, 0.0))

    def test_build_overlay_uses_red_at_critical_threshold(self):
        overlay = TemperatureOverlay._build_overlay(80.0)

        self.assertEqual((overlay.fg_color.r, overlay.fg_color.g, overlay.fg_color.b), (1.0, 0.0, 0.0))
