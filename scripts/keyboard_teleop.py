#!/usr/bin/env python

import rospy
import sys, select, tty, termios
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class UR5KeyboardTeleop:
    def __init__(self):
        rospy.init_node('ur5_keyboard_teleop')

        # 从你的 rostopic 列表中获取的控制器话题
        self.pub = rospy.Publisher('/eff_joint_traj_controller/command', JointTrajectory, queue_size=1)
        
        # 必须与控制器期望的顺序完全一致
        # 你可以通过 rostopic info /eff_joint_traj_controller/state 查看
        self.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]
        
        self.current_positions = [0.0] * 6
        self.has_received_state = False

        # 订阅 /joint_states 来获取当前位置
        rospy.Subscriber('/joint_states', JointState, self.joint_state_callback)

        rospy.loginfo("Waiting for first /joint_states message...")
        while not self.has_received_state:
            rospy.sleep(0.1)
        
        rospy.loginfo("Controller initialized. Ready to accept keyboard commands.")
        
        # 键盘控制映射
        self.key_map = {
            # 关节 0 (shoulder_pan)
            'q': (0, 0.1),  'a': (0, -0.1),
            # 关节 1 (shoulder_lift)
            'w': (1, 0.1),  's': (1, -0.1),
            # 关节 2 (elbow)
            'e': (2, 0.1),  'd': (2, -0.1),
            # 关节 3 (wrist_1)
            'r': (3, 0.1),  'f': (3, -0.1),
            # 关节 4 (wrist_2)
            't': (4, 0.1),  'g': (4, -0.1),
            # 关节 5 (wrist_3)
            'y': (5, 0.1),  'h': (5, -0.1),
        }

    def joint_state_callback(self, msg):
        """
        这个回调函数很关键。/joint_states 包含所有关节，
        我们必须按照 self.joint_names 的顺序来提取和存储它们。
        """
        try:
            # 创建一个 {关节名: 位置} 的字典
            pos_map = dict(zip(msg.name, msg.position))
            
            # 按照控制器要求的顺序重新排序
            new_positions = []
            for name in self.joint_names:
                new_positions.append(pos_map[name])
                
            self.current_positions = new_positions
            self.has_received_state = True
        except KeyError as e:
            rospy.logwarn_throttle(1, "Joint '{}' not found in /joint_states. Skipping update.".format(e))

    def get_key(self):
        """非阻塞式获取键盘输入的函数"""
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        return key

    def run(self):
        self.old_settings = termios.tcgetattr(sys.stdin)
        print("---------------------------")
        print("Keyboard Control for UR5 (Position)")
        print("---------------------------")
        print("Joint 0 (Pan):   q/a")
        print("Joint 1 (Lift):  w/s")
        print("Joint 2 (Elbow): e/d")
        print("Joint 3 (Wrist1): r/f")
        print("Joint 4 (Wrist2): t/g")
        print("Joint 5 (Wrist3): y/h")
        print("")
        print("Press 'x' to quit.")
        print("---------------------------")

        while not rospy.is_shutdown():
            key = self.get_key()
            
            if key == 'x':
                break
                
            if key in self.key_map:
                joint_index, increment = self.key_map[key]
                
                # 创建一个新的目标位置列表
                new_positions = list(self.current_positions)
                new_positions[joint_index] += increment
                
                self.send_goal(new_positions)
                
            rospy.sleep(0.01) # 短暂休眠，防止CPU占用过高

    def send_goal(self, positions):
        """发送单个点的轨迹"""
        traj = JointTrajectory()
        traj.header.stamp = rospy.Time.now()
        traj.joint_names = self.joint_names
        
        point = JointTrajectoryPoint()
        point.positions = positions
        # 给一个很短的执行时间，使其立即响应
        point.time_from_start = rospy.Duration(0.1) 
        
        traj.points.append(point)
        self.pub.publish(traj)

if __name__ == '__main__':
    try:
        teleop = UR5KeyboardTeleop()
        teleop.run()
    except rospy.ROSInterruptException:
        pass
    finally:
        # 恢复终端设置
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, teleop.old_settings)
