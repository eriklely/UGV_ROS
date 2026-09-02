#!/usr/bin/env python3
"""UGV UART driver.

This is the only process that opens /dev/ttyAMA0.

Commands:
  /cmd_vel          -> T:13
  /joint_commands   -> T:134
  /led_ctrl         -> T:132

Feedback (T:1001):
  /imu/data_raw, /imu/mag, /odom/odom_raw, /voltage, /joint_states

The driver never subscribes to /joint_states or /ugv/joint_states
for actuation.
"""
import json
import logging
import math
import os
import queue
import subprocess
import threading
import time

import serial

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState, MagneticField
from std_msgs.msg import Float32, Float32MultiArray, Header


DEFAULT_WAV = '/home/ws/ugv_ws/src/ugv_main/ugv_bringup/ugv_bringup/low_battery.wav'


class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def readline(self):
        """Return one newline-terminated frame, or None if none is ready.

        Never block: the ROS timer must not wait on UART.
        """
        i = self.buf.find(b'\n')
        if i >= 0:
            r = self.buf[:i + 1]
            self.buf = self.buf[i + 1:]
            return r
        n = min(512, self.s.in_waiting)
        if n <= 0:
            return None
        data = self.s.read(n)
        if not data:
            return None
        i = data.find(b'\n')
        if i >= 0:
            r = self.buf + data[:i + 1]
            self.buf[0:] = data[i + 1:]
            return r
        self.buf.extend(data)
        if len(self.buf) > 4096:
            self.buf.clear()
        return None

    def clear_buffer(self):
        self.buf.clear()
        self.s.reset_input_buffer()


class BaseController:
    def __init__(self, uart_dev_set, baud_set):
        self.logger = logging.getLogger('BaseController')
        self.ser = serial.Serial(uart_dev_set, baud_set, timeout=0.05)
        self.ser.reset_input_buffer()
        self.rl = ReadLine(self.ser)
        self.command_queue = queue.Queue()
        self.command_thread = threading.Thread(
            target=self.process_commands, daemon=True
        )
        self.command_thread.start()
        self.data_buffer = None
        self.base_data = {
            'T': 1001, 'L': 0, 'R': 0,
            'ax': 0, 'ay': 0, 'az': 0,
            'gx': 0, 'gy': 0, 'gz': 0,
            'mx': 0, 'my': 0, 'mz': 0,
            'odl': 0, 'odr': 0, 'v': 0,
        }
        self.pan_angle = 0.0
        self.tilt_angle = 0.0

    def feedback_data(self):
        line = None
        try:
            raw = self.rl.readline()
            if not raw:
                return None
            line = raw.decode('utf-8', errors='strict').strip()
            if not line:
                return None
            self.data_buffer = json.loads(line)
            self.base_data = self.data_buffer
            if (
                self.base_data.get('T') == 1001
                and 'pan' in self.base_data
                and 'tilt' in self.base_data
            ):
                self.pan_angle = float(self.base_data['pan'])
                self.tilt_angle = float(self.base_data['tilt'])
            return self.base_data
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self.logger.error(f'UART frame error: {e} with line: {line!r}')
            self.rl.clear_buffer()
        except Exception as e:
            self.logger.error(f'[base_ctrl.feedback_data] unexpected error: {e}')
            self.rl.clear_buffer()
        return None

    def on_data_received(self):
        self.ser.reset_input_buffer()
        raw = self.rl.readline()
        if not raw:
            return None
        return json.loads(raw.decode('utf-8'))

    def send_command(self, data):
        self.command_queue.put(data)

    def process_commands(self):
        while True:
            data = self.command_queue.get()
            self.ser.write((json.dumps(data) + '\n').encode('utf-8'))

    def base_json_ctrl(self, input_json):
        self.send_command(input_json)


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

        self.imu_data_raw_publisher_ = self.create_publisher(Imu, 'imu/data_raw', 100)
        self.imu_mag_publisher_ = self.create_publisher(MagneticField, 'imu/mag', 100)
        self.odom_publisher_ = self.create_publisher(Float32MultiArray, 'odom/odom_raw', 100)
        self.voltage_publisher_ = self.create_publisher(Float32, 'voltage', 50)
        self.joint_states_publisher_ = self.create_publisher(JointState, 'joint_states', 50)

        # Open UART once, here in __init__, never at import time.
        self.base_controller = BaseController('/dev/ttyAMA0', 115200)
        self.feedback_timer = self.create_timer(0.05, self.feedback_loop)

        self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.create_subscription(JointState, 'joint_commands', self.joint_commands_callback, 10)
        self.create_subscription(Float32MultiArray, 'led_ctrl', self.led_ctrl_callback, 10)

    def feedback_loop(self):
        if self.base_controller.feedback_data() is None:
            return
        if self.base_controller.base_data.get('T') == 1001:
            self.publish_imu_data_raw()
            self.publish_imu_mag()
            self.publish_odom_raw()
            self.publish_voltage()
            self.publish_joint_states()

    def publish_imu_data_raw(self):
        msg = Imu()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_imu_link'
        imu_raw_data = self.base_controller.base_data

        msg.linear_acceleration.x = 9.8 * float(imu_raw_data['ax']) / 8192
        msg.linear_acceleration.y = 9.8 * float(imu_raw_data['ay']) / 8192
        msg.linear_acceleration.z = 9.8 * float(imu_raw_data['az']) / 8192

        msg.angular_velocity.x = 3.1415926 * float(imu_raw_data['gx']) / (16.4 * 180)
        msg.angular_velocity.y = 3.1415926 * float(imu_raw_data['gy']) / (16.4 * 180)
        msg.angular_velocity.z = 3.1415926 * float(imu_raw_data['gz']) / (16.4 * 180)

        self.imu_data_raw_publisher_.publish(msg)

    def publish_imu_mag(self):
        msg = MagneticField()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_imu_link'
        imu_raw_data = self.base_controller.base_data

        msg.magnetic_field.x = float(imu_raw_data['mx']) * 0.15
        msg.magnetic_field.y = float(imu_raw_data['my']) * 0.15
        msg.magnetic_field.z = float(imu_raw_data['mz']) * 0.15

        self.imu_mag_publisher_.publish(msg)

    def publish_odom_raw(self):
        odom_raw_data = self.base_controller.base_data
        array = [odom_raw_data['odl'] / 100, odom_raw_data['odr'] / 100]
        msg = Float32MultiArray(data=array)
        self.odom_publisher_.publish(msg)

    def publish_voltage(self):
        voltage_data = self.base_controller.base_data
        msg = Float32()
        msg.data = float(voltage_data['v']) / 100
        self.voltage_publisher_.publish(msg)
        self._maybe_warn_voltage(msg.data)

    def publish_joint_states(self):
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = ''
        msg.name = ['pt_base_link_to_pt_link1', 'pt_link1_to_pt_link2']
        msg.position = [
            self.base_controller.pan_angle * math.pi / 180.0,
            self.base_controller.tilt_angle * math.pi / 180.0,
        ]
        self.joint_states_publisher_.publish(msg)

    def cmd_vel_callback(self, msg):
        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z
        epsilon = 1e-6
        if abs(linear_velocity) < epsilon:
            if 0 < angular_velocity < 0.2:
                angular_velocity = 0.2
            elif -0.2 < angular_velocity < 0:
                angular_velocity = -0.2
        self.base_controller.send_command({
            'T': '13',
            'X': linear_velocity,
            'Z': angular_velocity,
        })

    def joint_commands_callback(self, msg):
        try:
            x_rad = msg.position[msg.name.index('pt_base_link_to_pt_link1')]
            y_rad = msg.position[msg.name.index('pt_link1_to_pt_link2')]
        except ValueError:
            return
        self.base_controller.send_command({
            'T': 134,
            'X': (180 * x_rad) / 3.1415926,
            'Y': (180 * y_rad) / 3.1415926,
            'SX': 600,
            'SY': 600,
        })

    def led_ctrl_callback(self, msg):
        if len(msg.data) < 2:
            return
        self.base_controller.send_command({
            'T': 132,
            'IO4': msg.data[0],
            'IO5': msg.data[1],
        })

    def _maybe_warn_voltage(self, voltage_value):
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