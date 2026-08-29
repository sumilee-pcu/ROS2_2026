#!/usr/bin/env python3
# 5장 - 액션 클라이언트: 목표를 보내고 피드백과 결과를 받는다
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from example_interfaces.action import Fibonacci


class FibonacciClientNode(Node):
    def __init__(self):
        super().__init__("fibonacci_client")
        self.action_client_ = ActionClient(self, Fibonacci, "fibonacci")

    def send_goal(self, order):
        self.action_client_.wait_for_server()
        goal = Fibonacci.Goal()
        goal.order = order
        self.get_logger().info(f"목표 전송: order={order}")
        self.future_ = self.action_client_.send_goal_async(
            goal, feedback_callback=self.feedback_callback)
        self.future_.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info("목표가 거부되었다.")
            return
        self.get_logger().info("목표가 수락되었다.")
        self.result_future_ = goal_handle.get_result_async()
        self.result_future_.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        self.get_logger().info(f"피드백 수신: {feedback_msg.feedback.sequence}")

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f"결과: {result.sequence}")
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = FibonacciClientNode()
    node.send_goal(5)
    rclpy.spin(node)


if __name__ == "__main__":
    main()
