import math

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
from apriltag import apriltag


class ApriltagTracker(Node):
    def __init__(self):
        super().__init__('apriltag_tracker')

        self.bridge = CvBridge()
        self.detector = apriltag('tag36h11')

        self.last_t = self.get_clock().now()
        self.pan = 0.0
        self.tilt = 0.0
        self.turning = False
        self.panning = False

        self.create_subscription(Image, '/image_raw', self.image_callback, 10)
        self.apriltag_track_publisher = self.create_publisher(
            Image, '/apriltag_track/result', 10)
        self.gimbal_pub = self.create_publisher(JointState, '/joint_commands', 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

    def publish_gimbal(self, pan, tilt):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [
            'pt_base_link_to_pt_link1',
            'pt_link1_to_pt_link2',
        ]
        msg.position = [float(pan), float(tilt)]
        self.gimbal_pub.publish(msg)

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        results = self.detector.detect(gray)

        h, w = gray.shape[:2]
        cx0, cy0 = w // 2, h // 2
        dead_pan = 12
        dead_pan_hold = 4
        dead_tilt = 30
        pan_min, pan_max = -math.pi, math.pi
        tilt_min, tilt_max = -0.6, 0.8
        align_dead = math.radians(60)
        drive_dead = math.radians(8)
        max_wz = 1.2
        k_yaw = 2.5

        now = self.get_clock().now()
        dt = (now - self.last_t).nanoseconds / 1e9
        self.last_t = now
        dt = max(1e-3, min(dt, 0.1))

        k_pan = 0.024
        k_tilt = 0.014
        d_pan = 0.8
        d_tilt = 0.85
        max_dpan = 0.32
        max_dtilt = 0.21

        cmd = Twist()
        saw_tag = False

        for r in results:
            if r['id'] != 0:
                continue
            saw_tag = True

            corners = r['lb-rb-rt-lt'].astype(int)
            cv2.polylines(frame, [corners], True, (0, 255, 0), 2)
            center_x = int(r['center'][0])
            center_y = int(r['center'][1])
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

            ex = center_x - cx0
            ey = center_y - cy0

            if abs(ex) > dead_pan:
                self.panning = True
            elif abs(ex) < dead_pan_hold:
                self.panning = False

            if self.panning:
                dpan = k_pan * ex * dt
                dpan = max(-max_dpan, min(max_dpan, dpan))
                self.pan = (1.0 - d_pan) * self.pan + d_pan * (self.pan + dpan)
                self.pan = max(pan_min, min(pan_max, self.pan))

            if abs(ey) > dead_tilt:
                dtilt = -k_tilt * ey * dt
                dtilt = max(-max_dtilt, min(max_dtilt, dtilt))
                self.tilt = (1.0 - d_tilt) * self.tilt + d_tilt * (self.tilt + dtilt)
                self.tilt = max(tilt_min, min(tilt_max, self.tilt))

            if abs(self.pan) > align_dead:
                self.turning = True
            elif abs(self.pan) < drive_dead:
                self.turning = False

            if self.turning:
                cmd.angular.z = max(-max_wz, min(max_wz, -k_yaw * self.pan))
                # Unwind gimbal as the base turns so the camera stays on the tag.
                self.pan = self.pan + cmd.angular.z * dt
                self.pan = max(pan_min, min(pan_max, self.pan))
            elif abs(ex) < dead_pan and abs(ey) < dead_tilt:
                cmd.linear.x = 0.15

            self.publish_gimbal(self.pan, self.tilt)

            self.get_logger().info(
                f'pan={math.degrees(self.pan):.0f} deg  '
                f'wz={cmd.angular.z:.2f}  vx={cmd.linear.x:.2f}'
            )
            break

        if not saw_tag:
            self.publish_gimbal(self.pan, self.tilt)

        self.cmd_pub.publish(cmd)

        out = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.apriltag_track_publisher.publish(out)
        cv2.imshow('Tracked Image', frame)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = ApriltagTracker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()