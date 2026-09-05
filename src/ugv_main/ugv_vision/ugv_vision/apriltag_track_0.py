import math

import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
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
        self.move_delay_time = 2.0          # s: wait before body may move
        self.tag_seen_t = None              # time tag was first acquired this sighting
        self.last_seen_t = None             # last time tag id 0 was seen
        self.body_enabled = False           # latch: body is allowed to turn/drive
        self.turning = False
        self.driving = False
        self.panning = False

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.create_subscription(Image, '/image_raw', self.image_callback, qos)
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
        dead_pan = 28          # px: start gimbal pan if tag is this far left/right of center
        dead_pan_hold = 12     # px: stop gimbal pan once the tag is this close to center
        dead_tilt = 20         # px: start gimbal tilt if tag is this far above/below center
        pan_min, pan_max = -math.pi, math.pi          # rad: gimbal pan limits
        tilt_min, tilt_max = -math.radians(15), math.radians(90)  # rad: gimbal tilt limits
        align_dead = math.radians(60)  # rad: immediate body-enable if |pan| exceeds this
        yaw_start = math.radians(12)   # rad: start yaw once body is enabled
        yaw_stop = math.radians(6)     # rad: stop yaw once aligned enough
        drive_start = math.radians(12) # rad: start drive once heading is close
        drive_stop = math.radians(25)  # rad: stop drive if heading opens up again
        unseen_timeout = 0.3   # s: ignore brief dropouts; reset latch after this
        max_wz = 1.2           # rad/s: max body yaw rate (cmd_vel.angular.z clamp)
        k_yaw = 5            # 1/s: body turn gain, wz = -k_yaw * pan (then clamped by max_wz)
        vx = 0.15              # m/s: forward speed while driving

        now = self.get_clock().now()
        dt = (now - self.last_t).nanoseconds / 1e9
        self.last_t = now
        dt = max(1e-3, min(dt, 0.1))

        k_pan = 0.022          # gimbal pan speed vs pixel error (higher = snappier head yaw)
        k_tilt = 0.014         # gimbal tilt speed vs pixel error (higher = snappier head pitch)
        d_pan = 0.65           # 0–1: pan smoothing (1 = use new command fully, lower = more lag)
        d_tilt = 0.75          # 0–1: tilt smoothing (1 = use new command fully, lower = more lag)
        max_dpan = 0.33        # rad/frame: max pan step so the head cannot jump
        max_dtilt = 0.21       # rad/frame: max tilt step so the head cannot jump

        cmd = Twist()
        saw_tag = False

        for r in results:
            if r['id'] != 0:
                continue
            saw_tag = True
            self.last_seen_t = now

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

            if self.tag_seen_t is None:
                self.tag_seen_t = now
            held = (now - self.tag_seen_t).nanoseconds / 1e9

            if (not self.body_enabled) and (
                    abs(self.pan) > align_dead or held >= self.move_delay_time):
                self.body_enabled = True

            if self.body_enabled:
                if abs(self.pan) > yaw_start:
                    self.turning = True
                elif abs(self.pan) < yaw_stop:
                    self.turning = False

                if abs(self.pan) <= drive_start:
                    self.driving = True
                elif abs(self.pan) > drive_stop:
                    self.driving = False

                if self.turning:
                    cmd.angular.z = max(-max_wz, min(max_wz, -k_yaw * self.pan))
                    # Unwind gimbal as the base turns so the camera stays on the tag.
                    self.pan = self.pan + cmd.angular.z * dt
                    self.pan = max(pan_min, min(pan_max, self.pan))
                if self.driving:
                    cmd.linear.x = vx

            self.publish_gimbal(self.pan, self.tilt)

            break

        if not saw_tag:
            if self.last_seen_t is not None:
                unseen = (now - self.last_seen_t).nanoseconds / 1e9
                if unseen > unseen_timeout:
                    self.tag_seen_t = None
                    self.body_enabled = False
                    self.turning = False
                    self.driving = False
                    cmd = Twist()
                elif self.body_enabled:
                    if self.turning:
                        cmd.angular.z = max(-max_wz, min(max_wz, -k_yaw * self.pan))
                        self.pan = self.pan + cmd.angular.z * dt
                        self.pan = max(pan_min, min(pan_max, self.pan))
                    if self.driving:
                        cmd.linear.x = vx
            self.publish_gimbal(self.pan, self.tilt)

        self.cmd_pub.publish(cmd)

        out = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.apriltag_track_publisher.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ApriltagTracker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
