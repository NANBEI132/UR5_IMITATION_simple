#!/usr/bin/env python3
"""
主从遥操作 - 修复版（自动适配话题）
"""
import rospy
import numpy as np
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from collections import deque

class LeaderFollowerTeleop:
    def __init__(self):
        rospy.init_node('leader_follower_teleop')
        
        self.leader_topic = rospy.get_param('~leader_topic', '/leader/joint_states')
        self.control_rate = rospy.get_param('~control_rate', 100)
        
        self.joint_mapping = rospy.get_param('~joint_mapping', list(range(6)))
        self.position_scale = rospy.get_param('~position_scale', 1.0)
        
        self.leader_joints = None
        self.follower_joints = None
        
        self.filter_window = 5
        self.joint_buffer = deque(maxlen=self.filter_window)
        
        # 自动检测从手话题
        self.detect_topics()
        
        self.leader_sub = rospy.Subscriber(
            self.leader_topic,
            JointState,
            self.leader_callback
        )
        
        self.follower_sub = rospy.Subscriber(
            self.follower_joint_state_topic,
            JointState,
            self.follower_callback
        )
        
        self.command_pub = rospy.Publisher(
            self.follower_command_topic,
            JointTrajectory,
            queue_size=1
        )
        
        rospy.loginfo("Leader-Follower Teleoperation initialized")
        rospy.loginfo(f"Leader topic: {self.leader_topic}")
        rospy.loginfo(f"Follower state: {self.follower_joint_state_topic}")
        rospy.loginfo(f"Follower command: {self.follower_command_topic}")
    
    def detect_topics(self):
        """自动检测从手的话题"""
        rospy.loginfo("Detecting follower topics...")
        rospy.sleep(1.0)
        
        topics = rospy.get_published_topics()
        topic_names = [t[0] for t in topics]
        
        # 检测关节状态话题
        if '/ur5/joint_states' in topic_names:
            self.follower_joint_state_topic = '/ur5/joint_states'
        elif '/joint_states' in topic_names:
            self.follower_joint_state_topic = '/joint_states'
        else:
            self.follower_joint_state_topic = '/joint_states'
        
        # 检测控制命令话题
        command_candidates = [
            '/eff_joint_traj_controller/command',
            '/ur5/joint_group_position_controller/command',
            '/arm_controller/command'
        ]
        
        self.follower_command_topic = None
        for candidate in command_candidates:
            if candidate in topic_names:
                self.follower_command_topic = candidate
                break
        
        if self.follower_command_topic is None:
            self.follower_command_topic = '/eff_joint_traj_controller/command'
        
        rospy.loginfo(f"✓ Detected topics")
        
    def leader_callback(self, msg):
        if len(msg.position) >= 6:
            mapped_positions = [msg.position[i] * self.position_scale 
                              for i in self.joint_mapping]
            self.leader_joints = np.array(mapped_positions[:6])
            self.joint_buffer.append(self.leader_joints)
    
    def follower_callback(self, msg):
        if len(msg.position) >= 6:
            self.follower_joints = np.array(msg.position[:6])
    
    def smooth_joints(self):
        if len(self.joint_buffer) == 0:
            return None
        return np.mean(list(self.joint_buffer), axis=0)
    
    def send_command(self):
        if self.leader_joints is None:
            return
        
        smoothed_joints = self.smooth_joints()
        if smoothed_joints is None:
            return
        
        traj = JointTrajectory()
        traj.header.stamp = rospy.Time.now()
        traj.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]
        
        point = JointTrajectoryPoint()
        point.positions = smoothed_joints.tolist()
        point.velocities = [0.0] * 6
        point.time_from_start = rospy.Duration(1.0 / self.control_rate)
        
        traj.points = [point]
        self.command_pub.publish(traj)
        
    def run(self):
        rate = rospy.Rate(self.control_rate)
        
        rospy.loginfo("Waiting for leader data...")
        while self.leader_joints is None and not rospy.is_shutdown():
            rospy.sleep(0.1)
        
        rospy.loginfo("Teleoperation active!")
        
        while not rospy.is_shutdown():
            self.send_command()
            rate.sleep()

if __name__ == '__main__':
    try:
        teleop = LeaderFollowerTeleop()
        teleop.run()
    except rospy.ROSInterruptException:
        pass
