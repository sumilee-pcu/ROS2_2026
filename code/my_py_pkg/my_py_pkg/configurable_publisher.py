#!/usr/bin/env python3
# 6장 - 파라미터: number와 publish_period를 파라미터로 받는 퍼블리셔
#         7장 런치에서 이 노드에 파라미터를 주입하는 예제로도 쓴다
import rclpy
from rclpy.node import Node
from example_interfaces.msg import Int64


class ConfigurablePublisherNode(Node):
    def __init__(self):
        super().__init__("configurable_publisher")
        self.declare_parameter("number", 2)
        self.declare_parameter("publish_period", 1.0)

        self.number_ = self.get_parameter("number").value
        period = self.get_parameter("publish_period").value

        self.publisher_ = self.create_publisher(Int64, "number", 10)
        self.timer_ = self.create_timer(period, self.publish_number)
        self.get_logger().info(f"발행 주기 {period}s, 숫자 {self.number_}")

    def publish_number(self):
        msg = Int64()
        msg.data = self.number_
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ConfigurablePublisherNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
