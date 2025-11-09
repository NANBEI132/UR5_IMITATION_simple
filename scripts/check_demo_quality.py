#!/usr/bin/env python3
"""
数据质量检查工具
检查demonstrations的质量和一致性
"""

import h5py
import numpy as np
import glob
import os
from pathlib import Path
import matplotlib.pyplot as plt

class DemoQualityChecker:
    def __init__(self, demo_dir):
        self.demo_dir = demo_dir
        self.demos = []
        self.load_demos()
    
    def load_demos(self):
        """加载所有demonstrations"""
        demo_files = sorted(glob.glob(os.path.join(self.demo_dir, '*.h5')))
        
        print(f"Found {len(demo_files)} demonstration files")
        
        for filepath in demo_files:
            try:
                with h5py.File(filepath, 'r') as f:
                    demo = {
                        'filename': os.path.basename(filepath),
                        'joint_positions': np.array(f['joint_positions']),
                        'timestamps': np.array(f['timestamps']),
                        'num_samples': f.attrs['num_samples'],
                        'duration': f.attrs.get('duration', 0)
                    }
                    self.demos.append(demo)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        
        print(f"Successfully loaded {len(self.demos)} demonstrations\n")
    
    def check_basic_stats(self):
        """检查基本统计信息"""
        print("="*60)
        print("BASIC STATISTICS")
        print("="*60)
        
        durations = [d['duration'] for d in self.demos]
        samples = [d['num_samples'] for d in self.demos]
        
        print(f"Number of demonstrations: {len(self.demos)}")
        print(f"\nDuration (seconds):")
        print(f"  Min:  {min(durations):.2f}s")
        print(f"  Max:  {max(durations):.2f}s")
        print(f"  Mean: {np.mean(durations):.2f}s")
        print(f"  Std:  {np.std(durations):.2f}s")
        
        print(f"\nNumber of samples:")
        print(f"  Min:  {min(samples)}")
        print(f"  Max:  {max(samples)}")
        print(f"  Mean: {np.mean(samples):.0f}")
        
        # 检查是否有异常
        if max(durations) > 30:
            print(f"\n⚠ WARNING: Some demos are too long (>{30}s)")
        if min(durations) < 3:
            print(f"\n⚠ WARNING: Some demos are too short (<3s)")
        if np.std(durations) > 5:
            print(f"\n⚠ WARNING: Demo durations vary significantly")
        
        print()
    
    def check_joint_ranges(self):
        """检查关节运动范围"""
        print("="*60)
        print("JOINT RANGE ANALYSIS")
        print("="*60)
        
        joint_names = ['Shoulder Pan', 'Shoulder Lift', 'Elbow', 
                      'Wrist 1', 'Wrist 2', 'Wrist 3']
        
        all_positions = np.vstack([d['joint_positions'] for d in self.demos])
        
        for i in range(6):
            joint_data = all_positions[:, i]
            print(f"\nJoint {i} ({joint_names[i]}):")
            print(f"  Min:   {np.min(joint_data):7.3f} rad ({np.degrees(np.min(joint_data)):7.1f}°)")
            print(f"  Max:   {np.max(joint_data):7.3f} rad ({np.degrees(np.max(joint_data)):7.1f}°)")
            print(f"  Range: {np.max(joint_data) - np.min(joint_data):7.3f} rad")
            print(f"  Mean:  {np.mean(joint_data):7.3f} rad")
            print(f"  Std:   {np.std(joint_data):7.3f} rad")
            
            # 检查是否有关节几乎不动
            if np.std(joint_data) < 0.05:
                print(f"  ⚠ WARNING: Joint {i} barely moves (std < 0.05)")
        
        print()
    
    def check_smoothness(self):
        """检查轨迹平滑性"""
        print("="*60)
        print("SMOOTHNESS ANALYSIS")
        print("="*60)
        
        jerks = []
        
        for demo in self.demos:
            positions = demo['joint_positions']
            # 计算加速度（二阶差分）
            if len(positions) > 2:
                velocity = np.diff(positions, axis=0)
                acceleration = np.diff(velocity, axis=0)
                jerk = np.diff(acceleration, axis=0)
                
                # 平均jerk作为平滑性指标
                mean_jerk = np.mean(np.abs(jerk))
                jerks.append(mean_jerk)
        
        print(f"Average jerk (smoothness metric):")
        print(f"  Mean: {np.mean(jerks):.6f}")
        print(f"  Std:  {np.std(jerks):.6f}")
        
        # 找出最不平滑的demonstrations
        if len(jerks) > 0:
            threshold = np.mean(jerks) + 2*np.std(jerks)
            outliers = [i for i, j in enumerate(jerks) if j > threshold]
            
            if outliers:
                print(f"\n⚠ Potentially jerky demonstrations:")
                for idx in outliers:
                    print(f"  - {self.demos[idx]['filename']}")
        
        print()
    
    def check_consistency(self):
        """检查demonstrations之间的一致性"""
        print("="*60)
        print("CONSISTENCY ANALYSIS")
        print("="*60)
        
        # 检查起始位置的分布
        start_positions = np.array([d['joint_positions'][0] for d in self.demos])
        end_positions = np.array([d['joint_positions'][-1] for d in self.demos])
        
        print("Starting positions variance:")
        for i in range(6):
            std = np.std(start_positions[:, i])
            print(f"  Joint {i}: {std:.3f} rad")
            if std < 0.05:
                print(f"    ⚠ Very similar starting positions (std < 0.05)")
            elif std > 0.5:
                print(f"    ⚠ Very diverse starting positions (std > 0.5)")
        
        print("\nEnding positions variance:")
        for i in range(6):
            std = np.std(end_positions[:, i])
            print(f"  Joint {i}: {std:.3f} rad")
        
        print()
    
    def visualize(self, output_dir='./demo_analysis'):
        """可视化demonstrations"""
        print("="*60)
        print("VISUALIZATION")
        print("="*60)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 绘制所有demonstrations的轨迹
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        joint_names = ['Shoulder Pan', 'Shoulder Lift', 'Elbow', 
                      'Wrist 1', 'Wrist 2', 'Wrist 3']
        
        for i in range(6):
            ax = axes[i]
            for demo in self.demos:
                timestamps = demo['timestamps'] - demo['timestamps'][0]
                positions = demo['joint_positions'][:, i]
                ax.plot(timestamps, positions, alpha=0.5, linewidth=1)
            
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Position (rad)')
            ax.set_title(f'Joint {i}: {joint_names[i]}')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_file = os.path.join(output_dir, 'all_trajectories.png')
        plt.savefig(output_file, dpi=150)
        print(f"✓ Saved trajectory plot: {output_file}")
        
        # 绘制起始和结束位置的分布
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        start_positions = np.array([d['joint_positions'][0] for d in self.demos])
        end_positions = np.array([d['joint_positions'][-1] for d in self.demos])
        
        x = np.arange(6)
        ax1.boxplot([start_positions[:, i] for i in range(6)])
        ax1.set_xlabel('Joint Index')
        ax1.set_ylabel('Position (rad)')
        ax1.set_title('Starting Positions Distribution')
        ax1.grid(True, alpha=0.3)
        
        ax2.boxplot([end_positions[:, i] for i in range(6)])
        ax2.set_xlabel('Joint Index')
        ax2.set_ylabel('Position (rad)')
        ax2.set_title('Ending Positions Distribution')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_file = os.path.join(output_dir, 'position_distributions.png')
        plt.savefig(output_file, dpi=150)
        print(f"✓ Saved distribution plot: {output_file}")
        
        print()
    
    def generate_report(self):
        """生成完整报告"""
        print("\n")
        print("="*60)
        print("DEMONSTRATION QUALITY REPORT")
        print("="*60)
        print()
        
        self.check_basic_stats()
        self.check_joint_ranges()
        self.check_smoothness()
        self.check_consistency()
        self.visualize()
        
        # 综合评估
        print("="*60)
        print("OVERALL ASSESSMENT")
        print("="*60)
        
        num_demos = len(self.demos)
        
        if num_demos < 10:
            print("❌ INSUFFICIENT DATA: Need at least 10 demonstrations")
            print(f"   Current: {num_demos}, Need: {10 - num_demos} more")
        elif num_demos < 15:
            print("⚠ MINIMAL DATA: 10-15 demonstrations")
            print("   Recommendation: Collect 5-10 more for better results")
        elif num_demos < 25:
            print("✓ GOOD DATA: 15-25 demonstrations")
            print("   Should be sufficient for training")
        else:
            print("✓✓ EXCELLENT DATA: 25+ demonstrations")
            print("   Great dataset for training!")
        
        print("\nRecommendations:")
        print("1. Review plots in ./demo_analysis/")
        print("2. Remove any outlier demonstrations")
        print("3. Ensure task goals are clear and consistent")
        print("4. Ready for training!")
        print()


def main():
    import sys
    
    if len(sys.argv) > 1:
        demo_dir = sys.argv[1]
    else:
        demo_dir = os.path.expanduser('~/ur5_imitation_ws/src/ur5_imitation/demonstrations')
    
    if not os.path.exists(demo_dir):
        print(f"Error: Directory not found: {demo_dir}")
        print("Usage: python3 check_demo_quality.py [demo_directory]")
        return
    
    checker = DemoQualityChecker(demo_dir)
    checker.generate_report()


if __name__ == '__main__':
    main()
