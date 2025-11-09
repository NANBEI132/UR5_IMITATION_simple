#!/usr/bin/env python3
"""
话题诊断工具 - 找出正确的控制话题
"""
import rospy
import subprocess
import time
from std_msgs.msg import Float64MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

def get_all_topics():
    """获取所有话题"""
    result = subprocess.run(['rostopic', 'list'], capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def get_topic_type(topic):
    """获取话题类型"""
    result = subprocess.run(['rostopic', 'type', topic], capture_output=True, text=True)
    return result.stdout.strip()

def main():
    print("=" * 70)
    print("UR5 Topic Diagnostic Tool")
    print("=" * 70)
    print()
    
    # 获取所有话题
    all_topics = get_all_topics()
    
    # 查找相关话题
    print("1. JOINT STATE TOPICS (input):")
    print("-" * 70)
    joint_state_topics = [t for t in all_topics if 'joint_states' in t.lower()]
    if joint_state_topics:
        for topic in joint_state_topics:
            topic_type = get_topic_type(topic)
            print(f"  ✓ {topic}")
            print(f"    Type: {topic_type}")
    else:
        print("  ✗ No joint_states topics found!")
    print()
    
    # 查找命令话题
    print("2. COMMAND TOPICS (output):")
    print("-" * 70)
    command_topics = [t for t in all_topics if 'command' in t.lower() or 'controller' in t.lower()]
    
    if command_topics:
        for topic in command_topics:
            topic_type = get_topic_type(topic)
            print(f"  ✓ {topic}")
            print(f"    Type: {topic_type}")
    else:
        print("  ✗ No command topics found!")
    print()
    
    # 查找trajectory话题
    print("3. TRAJECTORY TOPICS:")
    print("-" * 70)
    trajectory_topics = [t for t in all_topics if 'trajectory' in t.lower()]
    
    if trajectory_topics:
        for topic in trajectory_topics:
            topic_type = get_topic_type(topic)
            print(f"  ✓ {topic}")
            print(f"    Type: {topic_type}")
    else:
        print("  ✗ No trajectory topics found!")
    print()
    
    # 推荐的话题
    print("=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)
    
    if joint_state_topics:
        print(f"\nFor INPUT (joint states), use:")
        print(f"  {joint_state_topics[0]}")
    
    # 查找最可能的输出话题
    output_candidates = []
    for topic in command_topics:
        if any(keyword in topic.lower() for keyword in ['arm', 'position', 'joint', 'group']):
            topic_type = get_topic_type(topic)
            output_candidates.append((topic, topic_type))
    
    if output_candidates:
        print(f"\nFor OUTPUT (commands), try these in order:")
        for i, (topic, topic_type) in enumerate(output_candidates, 1):
            print(f"  {i}. {topic}")
            print(f"     Type: {topic_type}")
    
    print()
    print("=" * 70)
    print("TESTING COMMANDS:")
    print("=" * 70)
    
    if output_candidates:
        for topic, topic_type in output_candidates[:3]:  # 只显示前3个
            print(f"\nTest {topic}:")
            if 'Float64MultiArray' in topic_type:
                print(f"  rostopic pub {topic} std_msgs/Float64MultiArray \"data: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]\" -1")
            elif 'JointTrajectory' in topic_type:
                print(f"  # This requires JointTrajectory message")
                print(f"  # Use the trajectory version of execute_policy.py")
    
    print()
    print("=" * 70)
    print("CONTROLLER STATUS:")
    print("=" * 70)
    
    # 检查控制器管理器
    try:
        result = subprocess.run(
            ['rosservice', 'call', '/controller_manager/list_controllers'],
            capture_output=True, text=True, timeout=2
        )
        print(result.stdout)
    except:
        print("✗ Cannot access controller manager")
    
    print()

if __name__ == '__main__':
    main()
