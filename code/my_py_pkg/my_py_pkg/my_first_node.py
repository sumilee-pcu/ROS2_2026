#!/usr/bin/env python3
# 2장 - 첫 노드: 1초마다 로그를 남기는 최소 노드
import rclpy
from rclpy.node import Node


class MyFirstNode(Node):
    def __init__(self):
        super().__init__("my_first_node")
        self.counter_ = 0
        self.get_logger().info("첫 노드가 시작되었다.")
        self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        self.counter_ += 1
        self.get_logger().info(f"안녕하세요 {self.counter_}")


def main(args=None):
    rclpy.init(args=args)
    node = MyFirstNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
