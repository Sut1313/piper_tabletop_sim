#!/usr/bin/env python3
"""Republish /joint_states as /joint_states_feedback for sim grasping.

The real Piper driver publishes /joint_states_feedback. Gazebo's
joint_state_broadcaster only publishes /joint_states, but the sim /joint_states
already contains the `gripper` joint (0..0.07 m total opening). The real
grasp_execute.py subscribes to /joint_states_feedback and looks for that name,
so this relay is enough.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class FeedbackRelay(Node):
    def __init__(self):
        super().__init__('joint_state_feedback_relay')
        self.pub = self.create_publisher(JointState, '/joint_states_feedback', 10)
        self.create_subscription(JointState, '/joint_states', self.cb, 10)
        self.get_logger().info('relaying /joint_states -> /joint_states_feedback')

    def cb(self, msg):
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = FeedbackRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
