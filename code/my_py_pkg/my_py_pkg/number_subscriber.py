#!/usr/bin/env python3
# 3장 - 토픽 구독: number 토픽의 Int64 값을 받아 로그로 출력
import rclpy
from rclpy.node import Node
from example_interfaces.msg import Int64


class NumberSubscriberNode(Node):
    def __init__(self):
        super().__init__("number_subscriber")
        self.subscriber_ = self.create_subscription(
            Int64, "number", self.callback_number, 10)
        self.get_logger().info("숫자 서브스크라이버가 시작되었다.")

    def callback_number(self, msg):
        self.get_logger().info(f"수신: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = NumberSubscriberNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
