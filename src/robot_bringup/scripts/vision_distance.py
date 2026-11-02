#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
import cv2
import numpy as np
import math


class YellowDetector:
    def __init__(self):
        self.lower = np.array([15, 40, 40])
        self.upper = np.array([50, 255, 255])
        self.min_area = 20

    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=2)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [(c, cv2.contourArea(c)) for c in cnts if cv2.contourArea(c) > self.min_area]
        contours.sort(key=lambda x: x[1], reverse=True)

        robot_center = None
        ball_center = None

        for c, area in contours:
            M = cv2.moments(c)
            if M['m00'] == 0:
                continue
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            if robot_center is None:
                robot_center = (cx, cy)
            elif ball_center is None:
                ball_center = (cx, cy)
                break

        return robot_center, ball_center


class DistanceCalculator:
    def __init__(self, camera_height, fov_h, img_width):
        self.camera_height = camera_height
        self.fov_h = fov_h
        self.img_width = img_width
        self.h_fov_m = 2.0 * camera_height * math.tan(fov_h / 2.0)
        self.pix_per_m = img_width / self.h_fov_m if self.h_fov_m > 0 else 1.0

    def compute(self, ball_center, robot_center):
        if ball_center is None or robot_center is None:
            return None
        dx = ball_center[0] - robot_center[0]
        dy = ball_center[1] - robot_center[1]
        dist_px = math.sqrt(dx * dx + dy * dy)
        return dist_px / self.pix_per_m


class AnnotationRenderer:
    @staticmethod
    def render(frame, robot_center, ball_center, dist_m):
        result = frame.copy()

        if ball_center:
            cv2.circle(result, ball_center, 8, (0, 0, 255), -1)
            cv2.circle(result, ball_center, 10, (255, 255, 255), 2)
            cv2.putText(result, 'Ball', (ball_center[0] - 24, ball_center[1] - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            cv2.putText(result, 'Ball', (ball_center[0] - 24, ball_center[1] - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)

        if robot_center:
            cv2.drawMarker(result, robot_center, (0, 255, 255), cv2.MARKER_CROSS, 16, 2)
            cv2.circle(result, robot_center, 6, (0, 255, 255), -1)
            cv2.putText(result, 'Robot', (robot_center[0] - 28, robot_center[1] - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        if ball_center and not robot_center:
            cv2.putText(result, 'Robot not found', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        elif robot_center and not ball_center:
            cv2.putText(result, 'Ball not found', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        elif not ball_center and not robot_center:
            cv2.putText(result, 'No objects detected', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return result


class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_distance')
        self.bridge = CvBridge()
        self.detector = YellowDetector()
        self.distance = DistanceCalculator(
            camera_height=2.43,
            fov_h=1.396,
            img_width=1280
        )
        self.renderer = AnnotationRenderer()

        self.sub = self.create_subscription(
            Image, '/overhead_camera/image_raw', self.image_cb, 10)
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_cb, 10)
        self.dist_pub = self.create_publisher(Float64, '/ball_distance', 10)
        self.ball_world_pub = self.create_publisher(Point, '/ball_world', 10)
        self.annotated_pub = self.create_publisher(Image, '/annotated_image', 10)

        self.latency_pub = self.create_publisher(Float64, '/latency_pong', 10)
        self.latency_sub = self.create_subscription(
            Float64, '/latency_ping', self.latency_cb, 10)

        self.robot_world_x = None
        self.robot_world_y = None

        self.declare_parameter('calib_scale_x', 0.75)
        self.declare_parameter('calib_scale_y', 0.48)

        self.get_logger().info(
            f'Vision distance node started (pix_per_m={self.distance.pix_per_m:.1f})')

    def latency_cb(self, msg):
        self.latency_pub.publish(msg)

    def odom_cb(self, msg):
        self.robot_world_x = msg.pose.pose.position.x
        self.robot_world_y = msg.pose.pose.position.y

    def image_cb(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'CV bridge error: {e}')
            return

        robot_center, ball_center = self.detector.detect(frame)
        dist_m = self.distance.compute(ball_center, robot_center)

        dist_msg = Float64()
        dist_msg.data = round(dist_m, 3) if dist_m is not None else float('nan')
        self.dist_pub.publish(dist_msg)

        ball_world = Point()
        if ball_center and robot_center and self.robot_world_x is not None:
            dx_px = ball_center[0] - robot_center[0]
            dy_px = ball_center[1] - robot_center[1]
            calib_x = self.get_parameter('calib_scale_x').value
            calib_y = self.get_parameter('calib_scale_y').value
            ball_world.x = self.robot_world_x + dx_px / (self.distance.pix_per_m * calib_x)
            ball_world.y = self.robot_world_y - dy_px / (self.distance.pix_per_m * calib_y)
        else:
            ball_world.x = float('nan')
            ball_world.y = float('nan')
        ball_world.z = 0.0
        self.ball_world_pub.publish(ball_world)

        result = self.renderer.render(frame, robot_center, ball_center, dist_m)
        self.annotated_pub.publish(self.bridge.cv2_to_imgmsg(result, 'bgr8'))


def main():
    rclpy.init()
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
