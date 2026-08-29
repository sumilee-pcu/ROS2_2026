#!/usr/bin/env python3
# 4장 - 서비스 클라이언트: 서버에 두 정수를 보내고 합을 받는다
import rclpy
from rclpy.node import Node
from example_interfaces.srv import AddTwoInts


class AddTwoIntsClientNode(Node):
    def __init__(self):
        super().__init__("add_two_ints_client")
        self.client_ = self.create_client(AddTwoInts, "add_two_ints")

    def send_request(self, a, b):
        while not self.client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("서버를 기다리는 중...")
        request = AddTwoInts.Request()
        request.a = a
        request.b = b
        future = self.client_.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        return future.result()


def main(args=None):
    rclpy.init(args=args)
    node = AddTwoIntsClientNode()
    response = node.send_request(3, 4)
    node.get_logger().info(f"결과: {response.sum}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
