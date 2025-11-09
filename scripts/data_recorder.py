#!/usr/bin/env python3
"""
数据记录器 - 修复版（自动适配话题）
"""
import rospy
import numpy as np
import h5py
from sensor_msgs.msg import JointState
import os
from datetime import datetime

class DemonstrationRecorder:
    def __init__(self):
        rospy.init_node('demonstration_recorder')
        
        self.save_dir = rospy.get_param('~save_dir', './demonstrations')
        self.record_frequency = rospy.get_param('~frequency', 50)
        
        os.makedirs(self.save_dir, exist_ok=True)
        
        self.joint_states = []
        self.timestamps = []
        self.is_recording = False
        
        # 自动检测关节状态话题
        self.detect_topics()
        
        self.joint_sub = rospy.Subscriber(
            self.joint_state_topic,
            JointState,
            self.joint_callback
        )
        
        rospy.loginfo("Demonstration Recorder initialized")
        rospy.loginfo(f"Subscribing to: {self.joint_state_topic}")
        rospy.loginfo("Service: rosservice call /start_recording to start")
        rospy.loginfo("Service: rosservice call /stop_recording to stop")
        
        # 创建服务
        from std_srvs.srv import Trigger, TriggerResponse
        rospy.Service('/start_recording', Trigger, self.start_recording_service)
        rospy.Service('/stop_recording', Trigger, self.stop_recording_service)
    
    def detect_topics(self):
        """自动检测关节状态话题"""
        rospy.loginfo("Detecting joint state topic...")
        rospy.sleep(1.0)
        
        topics = rospy.get_published_topics()
        topic_names = [t[0] for t in topics]
        
        # 优先使用ur5命名空间的话题
        if '/ur5/joint_states' in topic_names:
            self.joint_state_topic = '/ur5/joint_states'
        elif '/joint_states' in topic_names:
            self.joint_state_topic = '/joint_states'
        else:
            rospy.logwarn("No joint_states topic found, using default")
            self.joint_state_topic = '/joint_states'
        
        rospy.loginfo(f"✓ Using topic: {self.joint_state_topic}")
    
    def joint_callback(self, msg):
        """记录关节状态"""
        if not self.is_recording:
            return
            
        if len(msg.position) >= 6:
            self.joint_states.append(msg.position[:6])
            self.timestamps.append(rospy.Time.now().to_sec())
    
    def start_recording_service(self, req):
        from std_srvs.srv import TriggerResponse
        self.is_recording = True
        self.joint_states = []
        self.timestamps = []
        rospy.loginfo("🔴 Recording started...")
        return TriggerResponse(success=True, message="Recording started")
    
    def stop_recording_service(self, req):
        from std_srvs.srv import TriggerResponse
        self.is_recording = False
        rospy.loginfo("⏹️  Recording stopped")
        self.save_demonstration()
        return TriggerResponse(success=True, message="Recording stopped and saved")
    
    def save_demonstration(self):
        """保存示教数据到HDF5文件"""
        if len(self.joint_states) == 0:
            rospy.logwarn("No data to save!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.save_dir, f"demo_{timestamp}.h5")
        
        with h5py.File(filename, 'w') as f:
            f.create_dataset('joint_positions', data=np.array(self.joint_states))
            f.create_dataset('timestamps', data=np.array(self.timestamps))
            f.attrs['num_samples'] = len(self.joint_states)
            f.attrs['frequency'] = self.record_frequency
            f.attrs['duration'] = self.timestamps[-1] - self.timestamps[0]
        
        rospy.loginfo(f"✅ Saved {len(self.joint_states)} samples to {filename}")

if __name__ == '__main__':
    try:
        recorder = DemonstrationRecorder()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
