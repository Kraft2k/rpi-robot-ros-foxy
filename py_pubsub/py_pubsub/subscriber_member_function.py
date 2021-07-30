# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
import serial
from time import sleep
import rclpy
from rclpy.node import Node

import tf2_ros

from std_msgs.msg import String
from geometry_msgs.msg import Twist, PoseWithCovariance, TwistWithCovariance
from nav_msgs.msg import Odometry

@dataclass
class SerialStatus:
    """Class for different data given by the embedded system"""
    left_ref_speed: float
    right_ref_speed: float
    left_speed:float
    right_speed: float
    left_effort: float
    right_effor: float
    x_pos: float
    y_pos: float
    theta: float
    v: float
    w: float


class RobotControl(Node):

    def __init__(self):
        super().__init__('robot_control')
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.odom_publisher = self.create_publisher(Odometry, 'odom', 10)
        self.str_publisher = self.create_publisher(String, 'topic', 10)
        self.ser = serial.Serial('/dev/ttyACM0')    # open serial port
        self.get_logger().info(f'Using serial port {self.ser.name}')
        self.ser.write(b'0,0/')
        while self.ser.in_waiting == 0:
            self.get_logger().info(f'waiting response from serial port')
            sleep(0.0005)
        
        self.get_logger().info(f'init with state: "{self.ser.read(self.ser.in_waiting)}"')

    def send_command(self, linear: float, angular: float) -> SerialStatus:
        self.get_logger().info(f'Data to send: {linear}, {angular}')
        command = f'{linear:.2f},{angular:.2f}/'.encode('UTF-8')
        self.get_logger().info(f'Sending command: {command}')
        self.ser.write(command)
        while self.ser.in_waiting == 0:
            pass
        
        res = self.ser.read(self.ser.in_waiting)
        raw_list = res.split(',')
        values_list = [float(value) for value in raw_list]
        return SerialStatus(*values_list)

    def listener_callback(self, twist: Twist):
        msg = String()
        odom_msg = Odometry()
        msg.data = 'hola!'
        self.get_logger().info(f'Received: {twist}')
        self.get_logger().info(f'Publish!')
        self.str_publisher.publish(msg)
        status = self.send_command(twist.linear.x, twist.angular.z)
        # odom_msg.pose.pose.orientation.
        # tf2_ros.T
        self.get_logger().info(f'Received from robot: {status}')


def main(args=None):
    rclpy.init(args=args)

    robot_control = RobotControl()

    rclpy.spin(robot_control)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    robot_control.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()