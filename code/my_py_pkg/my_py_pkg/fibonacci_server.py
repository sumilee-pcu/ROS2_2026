#!/usr/bin/env python3
# 5장 - 액션 서버: 목표 order까지 피보나치 수열을 계산하며 피드백을 발행
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from example_interfaces.action import Fibonacci


class FibonacciServerNode(Node):
    def __init__(self):
        super().__init__("fibonacci_server")
        self.action_server_ = ActionServer(
            self, Fibonacci, "fibonacci", self.execute_callback)
        self.get_logger().info("피보나치 액션 서버가 시작되었다.")

    def execute_callback(self, goal_handle):
        feedback = Fibonacci.Feedback()
        feedback.sequence = [0, 1]
        for i in range(1, goal_handle.request.order):
            feedback.sequence.append(
                feedback.sequence[i] + feedback.sequence[i - 1])
            goal_handle.publish_feedback(feedback)
            self.get_logger().info(f"피드백: {feedback.sequence}")
            time.sleep(1.0)
        goal_handle.succeed()
        result = Fibonacci.Result()
        result.sequence = feedback.sequence
        return result


def main(args=None):
    rclpy.init(args=args)
    node = FibonacciServerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
