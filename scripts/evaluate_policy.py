#!/usr/bin/env python3
"""
评估训练好的模仿学习策略
"""

import torch
import numpy as np
import h5py
import glob
import os
from models.bc_network import BCPolicy, LSTMBCPolicy
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error

class PolicyEvaluator:
    def __init__(self, model_path, test_data_dir):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 加载模型
        checkpoint = torch.load(model_path, map_location=self.device)
        self.config = checkpoint['config']
        
        if self.config['sequence_length'] > 1:
            self.model = LSTMBCPolicy(
                state_dim=6,
                action_dim=6,
                hidden_dim=self.config['hidden_dim'],
                sequence_length=self.config['sequence_length']
            ).to(self.device)
        else:
            self.model = BCPolicy(
                state_dim=6,
                action_dim=6,
                hidden_dims=self.config['hidden_dims']
            ).to(self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        # 加载测试数据
        self.test_files = glob.glob(os.path.join(test_data_dir, '*.h5'))
        print(f"Found {len(self.test_files)} test demonstrations")
    
    def load_test_data(self):
        """加载测试数据"""
        all_states = []
        all_actions = []
        
        for test_file in self.test_files:
            with h5py.File(test_file, 'r') as f:
                joint_positions = f['joint_positions'][:]
                states = joint_positions[:-1]
                actions = joint_positions[1:]
                
                if self.config.get('use_velocity', False):
                    actions = actions - states
                
                all_states.append(states)
                all_actions.append(actions)
        
        return all_states, all_actions
    
    def evaluate_accuracy(self):
        """评估预测精度"""
        states_list, actions_list = self.load_test_data()
        
        all_mse = []
        all_mae = []
        joint_wise_errors = [[] for _ in range(6)]
        
        with torch.no_grad():
            for states, ground_truth_actions in zip(states_list, actions_list):
                # 预测
                if self.config['sequence_length'] > 1:
                    # 处理序列数据
                    predictions = []
                    for i in range(len(states) - self.config['sequence_length'] + 1):
                        seq = states[i:i+self.config['sequence_length']]
                        state_tensor = torch.FloatTensor(seq).unsqueeze(0).to(self.device)
                        pred = self.model(state_tensor).cpu().numpy()[0]
                        predictions.append(pred)
                    predictions = np.array(predictions)
                    ground_truth_actions = ground_truth_actions[self.config['sequence_length']-1:]
                else:
                    state_tensor = torch.FloatTensor(states).to(self.device)
                    predictions = self.model(state_tensor).cpu().numpy()
                
                # 计算误差
                mse = mean_squared_error(ground_truth_actions, predictions)
                mae = mean_absolute_error(ground_truth_actions, predictions)
                
                all_mse.append(mse)
                all_mae.append(mae)
                
                # 每个关节的误差
                for j in range(6):
                    joint_error = np.abs(ground_truth_actions[:, j] - predictions[:, j])
                    joint_wise_errors[j].extend(joint_error)
        
        # 统计结果
        results = {
            'mean_mse': np.mean(all_mse),
            'std_mse': np.std(all_mse),
            'mean_mae': np.mean(all_mae),
            'std_mae': np.std(all_mae),
            'joint_mae': [np.mean(errors) for errors in joint_wise_errors]
        }
        
        return results, joint_wise_errors
    
    def plot_predictions(self, demo_idx=0):
        """可视化一个demonstration的预测结果"""
        states_list, actions_list = self.load_test_data()
        
        if demo_idx >= len(states_list):
            print(f"Invalid demo index. Max: {len(states_list)-1}")
            return
        
        states = states_list[demo_idx]
        ground_truth = actions_list[demo_idx]
        
        # 预测
        with torch.no_grad():
            if self.config['sequence_length'] > 1:
                predictions = []
                for i in range(len(states) - self.config['sequence_length'] + 1):
                    seq = states[i:i+self.config['sequence_length']]
                    state_tensor = torch.FloatTensor(seq).unsqueeze(0).to(self.device)
                    pred = self.model(state_tensor).cpu().numpy()[0]
                    predictions.append(pred)
                predictions = np.array(predictions)
                ground_truth = ground_truth[self.config['sequence_length']-1:]
            else:
                state_tensor = torch.FloatTensor(states).to(self.device)
                predictions = self.model(state_tensor).cpu().numpy()
        
        # 绘图
        joint_names = ['Shoulder Pan', 'Shoulder Lift', 'Elbow', 
                      'Wrist 1', 'Wrist 2', 'Wrist 3']
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        axes = axes.flatten()
        
        for i in range(6):
            axes[i].plot(ground_truth[:, i], label='Ground Truth', linewidth=2)
            axes[i].plot(predictions[:, i], label='Prediction', linewidth=2, linestyle='--')
            axes[i].set_title(joint_names[i])
            axes[i].set_xlabel('Timestep')
            axes[i].set_ylabel('Position (rad)')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('prediction_comparison.png', dpi=150)
        print("Saved prediction plot to prediction_comparison.png")
        plt.show()
    
    def plot_error_distribution(self, joint_wise_errors):
        """绘制误差分布"""
        joint_names = ['Shoulder\nPan', 'Shoulder\nLift', 'Elbow', 
                      'Wrist 1', 'Wrist 2', 'Wrist 3']
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        axes = axes.flatten()
        
        for i in range(6):
            axes[i].hist(joint_wise_errors[i], bins=50, alpha=0.7, edgecolor='black')
            axes[i].axvline(np.mean(joint_wise_errors[i]), color='r', 
                          linestyle='--', linewidth=2, label='Mean')
            axes[i].set_title(f'{joint_names[i]}\nMAE: {np.mean(joint_wise_errors[i]):.4f} rad')
            axes[i].set_xlabel('Absolute Error (rad)')
            axes[i].set_ylabel('Frequency')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('error_distribution.png', dpi=150)
        print("Saved error distribution plot to error_distribution.png")
        plt.show()
    
    def print_report(self, results):
        """打印评估报告"""
        print("\n" + "="*60)
        print("  Policy Evaluation Report")
        print("="*60)
        print(f"\nOverall Metrics:")
        print(f"  Mean Squared Error:  {results['mean_mse']:.6f} ± {results['std_mse']:.6f}")
        print(f"  Mean Absolute Error: {results['mean_mae']:.6f} ± {results['std_mae']:.6f}")
        
        print(f"\nPer-Joint Mean Absolute Error (rad):")
        joint_names = ['Shoulder Pan', 'Shoulder Lift', 'Elbow', 
                      'Wrist 1', 'Wrist 2', 'Wrist 3']
        for name, mae in zip(joint_names, results['joint_mae']):
            print(f"  {name:15s}: {mae:.6f} rad ({np.degrees(mae):.2f}°)")
        
        print("="*60 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate trained BC policy')
    parser.add_argument('model_path', type=str, help='Path to trained model')
    parser.add_argument('test_data_dir', type=str, help='Directory containing test demonstrations')
    parser.add_argument('--plot', action='store_true', help='Generate plots')
    parser.add_argument('--demo-idx', type=int, default=0, help='Demo index for visualization')
    
    args = parser.parse_args()
    
    # 创建评估器
    evaluator = PolicyEvaluator(args.model_path, args.test_data_dir)
    
    # 评估精度
    print("Evaluating policy accuracy...")
    results, joint_wise_errors = evaluator.evaluate_accuracy()
    
    # 打印报告
    evaluator.print_report(results)
    
    # 可视化
    if args.plot:
        print("Generating plots...")
        evaluator.plot_predictions(args.demo_idx)
        evaluator.plot_error_distribution(joint_wise_errors)


if __name__ == '__main__':
    main()
