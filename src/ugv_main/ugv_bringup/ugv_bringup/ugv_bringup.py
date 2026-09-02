#!/usr/bin/env python3
"""Legacy UART node.

Serial, BaseController, and command callbacks now live in ugv_driver.
This executable remains so old launch files do not crash. It does not
open /dev/ttyAMA0.
"""
import rclpy
from rclpy.node import Node


class ugv_bringup(Node):
    def __init__(self):
        super().__init__('ugv_bringup')
        self.get_logger().warn(
            'ugv_bringup is a stub. UART, cmd_vel, joint_commands and LED '
            'are handled by ugv_driver only. Serial port is not opened.'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ugv_bringup()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()