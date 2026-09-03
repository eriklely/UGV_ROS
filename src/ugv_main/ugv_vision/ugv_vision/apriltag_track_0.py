import json
import time
import math
import math

import cv2
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState
from cv_bridge import CvBridge
from ugv_interface.action import Behavior
from apriltag import apriltag


class ApriltagTracker(Node):
    def __init__(self):
        super().__init__('apriltag_tracker')

        self.bridge = CvBridge()
        self.detector = apriltag('tag36h11')

        self.pan = 0.0
        self.tilt = 0.0
        self.last_body_cmd = None
        self.last_body_time = 0.0

        self.create_subscription(Image, '/image_raw', self.image_callback, 10)
        self.apriltag_track_publisher = self.create_publisher(
            Image, '/apriltag_track/result', 10)
        self.gimbal_pub = self.create_publisher(JointState, '/joint_commands', 10)
        self._action_client = ActionClient(self, Behavior, 'behavior')

    def publish_gimbal(self, pan, tilt):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [
            'pt_base_link_to_pt_link1',
            'pt_link1_to_pt_link2',
        ]
        msg.position = [float(pan), float(tilt)]
        self.gimbal_pub.publish(msg)

    def send_goal(self, command):
        now = time.time()
        if command == self.last_body_cmd and (now - self.last_body_time) < 0.4:
            return
        if not self._action_client.wait_for_server(timeout_sec=0.1):
            self.get_logger().warn('behavior server not up')
            return

        goal_msg = Behavior.Goal()
        goal_msg.command = command
        self._action_client.send_goal_async(goal_msg)
        self.last_body_cmd = command
        self.last_body_time = now

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        results = self.detector.detect(gray)

        h, w = gray.shape[:2]
        cx0, cy0 = w // 2, h // 2
        dead = 20
        k_pan, k_tilt = 0.002, 0.002
        pan_min, pan_max = -1.2, 1.2
        tilt_min, tilt_max = -0.6, 0.8

        for r in results:
            if r['id'] != 0:
                continue

            corners = r['lb-rb-rt-lt'].astype(int)
            cv2.polylines(frame, [corners], True, (0, 255, 0), 2)
            center_x, center_y = int(r['center'][0]), int(r['center'][1])
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

            ex = center_x - cx0
            ey = center_y - cy0

            if abs(ex) > dead:
                self.pan = max(pan_min, min(pan_max, self.pan + k_pan * ex))
            if abs(ey) > dead:
                self.tilt = max(tilt_min, min(tilt_max, self.tilt - k_tilt * ey))

            self.publish_gimbal(self.pan, self.tilt)

            turn_start = math.radians(70)

            if self.pan >= turn_start:
                body = [{'T': 1, 'type': 'spin', 'data': -0.4}]   # flip data if wrong way
            elif self.pan <= -turn_start:
                body = [{'T': 1, 'type': 'spin', 'data': 0.4}]
            elif abs(ex) < dead and abs(ey) < dead:
                body = [{'T': 1, 'type': 'drive_on_heading', 'data': 0.01}]
            else:
                body = [{'T': 1, 'type': 'stop', 'data': 0}]

            self.send_goal(json.dumps(body))
            break

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