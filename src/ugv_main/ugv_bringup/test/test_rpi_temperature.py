"""Unit tests for the Raspberry Pi temperature publisher helpers."""

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

if 'sensor_msgs.msg' not in sys.modules:
    sensor_msgs_module = types.ModuleType('sensor_msgs')
    sensor_msgs_msg_module = types.ModuleType('sensor_msgs.msg')
    sensor_msgs_msg_module.Temperature = type('Temperature', (), {})
    sensor_msgs_module.msg = sensor_msgs_msg_module
    sys.modules['sensor_msgs'] = sensor_msgs_module
    sys.modules['sensor_msgs.msg'] = sensor_msgs_msg_module

if 'std_msgs.msg' not in sys.modules:
    std_msgs_module = types.ModuleType('std_msgs')
    std_msgs_msg_module = types.ModuleType('std_msgs.msg')
    std_msgs_msg_module.Float32 = type('Float32', (), {})
    std_msgs_module.msg = std_msgs_msg_module
    sys.modules['std_msgs'] = std_msgs_module
    sys.modules['std_msgs.msg'] = std_msgs_msg_module

from ugv_bringup.rpi_temperature import RpiTemperaturePublisher


class RpiTemperaturePublisherTests(unittest.TestCase):
    def test_parse_vcgencmd_output(self):
        self.assertEqual(
            RpiTemperaturePublisher._parse_vcgencmd_output("temp=48.5'C"),
            48.5,
        )

    def test_parse_vcgencmd_output_invalid(self):
        with self.assertRaises(ValueError):
            RpiTemperaturePublisher._parse_vcgencmd_output('unexpected')

    def test_read_temperature_c_prefers_sysfs(self):
        publisher = object.__new__(RpiTemperaturePublisher)
        publisher._read_sysfs_temperature = lambda: 51.25
        publisher._read_vcgencmd_temperature = self.fail

        self.assertEqual(publisher._read_temperature_c(), 51.25)

    def test_read_temperature_c_falls_back_to_vcgencmd(self):
        publisher = object.__new__(RpiTemperaturePublisher)

        def raise_missing_file():
            raise FileNotFoundError('missing thermal sysfs')

        publisher._read_sysfs_temperature = raise_missing_file
        publisher._read_vcgencmd_temperature = lambda: 52.75

        self.assertEqual(publisher._read_temperature_c(), 52.75)
