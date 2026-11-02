#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import requests
import math


class OdomData:
    # Extract and round odometry fields: position, yaw, speed, turn rate
    def __init__(self, position, orientation, twist_linear, twist_angular):
        self.x = round(position.x, 4)
        self.y = round(position.y, 4)
        self.yaw = round(self._quat_to_yaw(orientation), 4)
        self.speed = round(twist_linear.x, 4)
        self.turn_rate = round(twist_angular.z, 4)

    @staticmethod
    def _quat_to_yaw(o):
        # Convert quaternion to yaw angle (radians)
        siny_cosp = 2 * (o.w * o.z + o.x * o.y)
        cosy_cosp = 1 - 2 * (o.y * o.y + o.z * o.z)
        return math.atan2(siny_cosp, cosy_cosp)

    # Serialize to JSON-compatible dict for HTTP transmission
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "yaw": self.yaw,
            "speed": self.speed,
            "turn_rate": self.turn_rate,
        }


class HttpClient:
    VPS_URL = "http://xxx.xxx.xxx.xxx/api/odom"

    @staticmethod
    def post_odom(data):
        # POST odometry data to VPS API; silently ignore failures
        try:
            requests.post(HttpClient.VPS_URL, json=data, timeout=1)
        except Exception as e:
            pass


class Ros2ToHttp(Node):
    def __init__(self):
        super().__init__('ros2_to_http')
        # Subscribe to ROS odometry and forward to HTTP endpoint
        self.sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.get_logger().info('ros2_to_http node started')

    def odom_cb(self, msg):
        odom = OdomData(
            position=msg.pose.pose.position,
            orientation=msg.pose.pose.orientation,
            twist_linear=msg.twist.twist.linear,
            twist_angular=msg.twist.twist.angular,
        )
        HttpClient.post_odom(odom.to_dict())


def main():
    # Initialize ROS2, spin the HTTP relay node, and clean up on shutdown
    rclpy.init()
    node = Ros2ToHttp()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
