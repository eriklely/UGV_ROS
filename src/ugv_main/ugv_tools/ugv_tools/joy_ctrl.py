#!/usr/bin/env python3
# encoding: utf-8

import getpass
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy, JointState
import pygame


PAN_JOINT = 'pt_base_link_to_pt_link1'
TILT_JOINT = 'pt_link1_to_pt_link2'


def get_joystick_names():
    pygame.init()
    pygame.joystick.init()
    names = []
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        j.init()
        names.append(j.get_name())
    pygame.quit()
    return names


class JoyTeleop(Node):
    def __init__(self, name):
        super().__init__(name)
        self.Joy_active = True
        self.user_name = getpass.getuser()
        self.linear_Gear = 1.0
        self.angular_Gear = 1.0

        self.pub_cmdVel = self.create_publisher(Twist, 'cmd_vel', 10)
        self.pt_pub = self.create_publisher(JointState, 'joint_commands', 10)

        self.create_subscription(Joy, 'joy', self.callback, 10)
        # Measured pose from ugv_driver (baseboard feedback)
        self.create_subscription(JointState, 'joint_states', self.on_joint_states, 10)

        self.declare_parameter('xspeed_limit', 0.5)
        self.declare_parameter('angular_speed_limit', 5.0)
        self.xspeed_limit = self.get_parameter('xspeed_limit').value
        self.angular_speed_limit = self.get_parameter('angular_speed_limit').value

        names = get_joystick_names()
        self.joysticks = names[0] if names else "Xbox 360 Controller"
        self.get_logger().info(f"Using joystick: {self.joysticks}")

        # Camera command state (radians)
        self.pan = 0.0
        self.tilt = 0.0
        self.pt_step = 0.05
        self.have_feedback = False
        self.prev_center_btn = 0

    def on_joint_states(self, msg: JointState):
        # Seed the stick integrator from the real gimbal once,
        # so the first move is not relative to an assumed zero.
        if self.have_feedback:
            return
        try:
            self.pan = float(msg.position[msg.name.index(PAN_JOINT)])
            self.tilt = float(msg.position[msg.name.index(TILT_JOINT)])
            self.have_feedback = True
            self.get_logger().info(
                f'Seeded pan/tilt from feedback: pan={self.pan:.3f} tilt={self.tilt:.3f}'
            )
        except ValueError:
            return

    def publish_pt(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [PAN_JOINT, TILT_JOINT]
        msg.position = [float(self.pan), float(self.tilt)]
        self.pt_pub.publish(msg)

    def filter_data(self, v):
        return 0.0 if abs(v) < 0.18 else v

    def callback(self, msg: Joy):
        if len(msg.axes) < 4:
            return

        # ===== LEFT STICK → Driving =====
        lin = self.filter_data(msg.axes[1]) * self.xspeed_limit * self.linear_Gear
        ang = self.filter_data(msg.axes[0]) * self.angular_speed_limit * self.angular_Gear

        twist = Twist()
        twist.linear.x = max(min(lin, self.xspeed_limit), -self.xspeed_limit)
        twist.angular.z = max(min(ang, self.angular_speed_limit), -self.angular_speed_limit)

        if self.Joy_active:
            self.pub_cmdVel.publish(twist)

        # ===== RS click → Center camera once =====
        # game_controller_node Xbox mapping: button 10 is right-stick click, not R1
        center_btn = msg.buttons[10] if len(msg.buttons) > 10 else 0
        if center_btn == 1 and self.prev_center_btn == 0:
            self.pan = 0.0
            self.tilt = 0.0
            self.publish_pt()
            self.prev_center_btn = center_btn
            return
        self.prev_center_btn = center_btn

        # ===== RIGHT STICK → Camera (rate control) =====
        # Centered stick must HOLD the last command, not publish zero.
        dpan = -self.filter_data(msg.axes[2]) * self.pt_step
        dtilt = self.filter_data(msg.axes[3]) * self.pt_step
        if dpan == 0.0 and dtilt == 0.0:
            return

        self.pan = max(-3.0, min(3.0, self.pan + dpan))
        self.tilt = max(-0.7, min(1.4, self.tilt + dtilt))
        self.publish_pt()


def main(args=None):
    rclpy.init(args=args)
    node = JoyTeleop('joy_ctrl')
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()