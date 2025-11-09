#!/usr/bin/env python3
"""
执行训练好的策略 - 定制版
专门匹配 /eff_joint_traj_controller/command
"""
import rospy
import torch
import numpy as np
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import sys
import os

# 添加父目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from models.bc_network import BCPolicy, LSTMBCPolicy

class PolicyExecutor:
    def __init__(self, model_path):
        rospy.init_node('policy_executor')
        
        print("=" * 60)
        print("Policy Executor - Custom for eff_joint_traj_controller")
        print("=" * 60)
        print(f"Loading policy from: {model_path}")
        
        # 检测设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Device: {self.device}")
        
        # 加载模型
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        
        # 兼容不同的保存格式
        if isinstance(checkpoint, dict):
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            else:
                state_dict = checkpoint
        else:
            state_dict = checkpoint
        
        # 创建模型
        state_dim = 6
        action_dim = 6
        
        self.policy = BCPolicy(state_dim, action_dim)
        self.policy.load_state_dict(state_dict)
        self.policy.to(self.device)
        self.policy.eval()
        
        print("✓ Policy loaded successfully")
        print("=" * 60)
        print()
        
        # 当前关节状态
        self.current_joint_state = None
        self.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]
        
        # 使用正确的话题！
        self.joint_state_topic = '/joint_states'
        self.command_topic = '/eff_joint_traj_controller/command'
        
        # 订阅关节状态
        self.joint_sub = rospy.Subscriber(
            self.joint_state_topic,
            JointState,
            self.joint_state_callback,
            queue_size=1
        )
        
        # 发布trajectory命令
        self.traj_pub = rospy.Publisher(
            self.command_topic,
            JointTrajectory,
            queue_size=10
        )
        
        # 执行频率
        self.rate = rospy.Rate(20)  # 20 Hz
        
        print(f"✓ Subscribed to: {self.joint_state_topic}")
        print(f"✓ Publishing to: {self.command_topic}")
        print("Waiting for joint states...")
        print()
        
        # 等待joint states
        rospy.sleep(1.0)
    
    def joint_state_callback(self, msg):
        """接收关节状态"""
        if len(msg.position) >= 6:
            self.current_joint_state = np.array(msg.position[:6])
    
    def execute_policy(self):
        """执行策略"""
        print("=" * 60)
        print("Starting Policy Execution")
        print("=" * 60)
        print(f"Publishing trajectory commands at 20 Hz")
        print("Press Ctrl+C to stop")
        print()
        
        step_count = 0
        
        # 等待第一个关节状态
        while self.current_joint_state is None and not rospy.is_shutdown():
            rospy.logwarn_throttle(2.0, "Waiting for joint states...")
            rospy.sleep(0.1)
        
        if self.current_joint_state is None:
            rospy.logerr("No joint states received!")
            return
        
        print("✓ Received joint states, starting execution...")
        print()
        
        while not rospy.is_shutdown():
            # 使用策略预测下一个动作
            with torch.no_grad():
                state_tensor = torch.FloatTensor(self.current_joint_state).unsqueeze(0).to(self.device)
                action = self.policy(state_tensor)
                action = action.cpu().numpy().flatten()
            
            # 创建trajectory消息
            traj_msg = JointTrajectory()
            traj_msg.header.stamp = rospy.Time.now()
            traj_msg.joint_names = self.joint_names
            
            # 创建trajectory point
            point = JointTrajectoryPoint()
            point.positions = action.tolist()
            point.velocities = [0.0] * 6  # 可选：设置速度
            point.time_from_start = rospy.Duration(0.05)  # 50ms
            
            traj_msg.points = [point]
            
            # 发布命令
            self.traj_pub.publish(traj_msg)
            
            step_count += 1
            
            # 每1秒打印一次状态（20步）
            if step_count % 20 == 0:
                diff = np.abs(self.current_joint_state - action)
                max_diff = np.max(diff)
                print(f"Step {step_count:4d}: "
                      f"Current: [{self.current_joint_state[0]:+.3f}, {self.current_joint_state[1]:+.3f}, {self.current_joint_state[2]:+.3f}, ...], "
                      f"Target: [{action[0]:+.3f}, {action[1]:+.3f}, {action[2]:+.3f}, ...], "
                      f"Max diff: {max_diff:.4f}")
            
            self.rate.sleep()

def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Usage:")
        print("=" * 60)
        print("  rosrun ur5_imitation execute_policy.py <model_path>")
        print()
        print("Example:")
        print("  rosrun ur5_imitation execute_policy.py \\")
        print("    ~/ur5_imitation_ws/src/ur5_imitation/models/bc_policy_best.pth")
        print("=" * 60)
        sys.exit(1)
    
    model_path = sys.argv[1]
    
    # 扩展路径
    model_path = os.path.expanduser(model_path)
    
    # 检查文件是否存在
    if not os.path.exists(model_path):
        print(f"Error: Model file not found: {model_path}")
        sys.exit(1)
    
    try:
        executor = PolicyExecutor(model_path)
        executor.execute_policy()
    except rospy.ROSInterruptException:
        print()
        print("=" * 60)
        print("Policy execution stopped by ROS")
        print("=" * 60)
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("Policy execution interrupted by user")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
