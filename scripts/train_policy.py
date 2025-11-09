#!/usr/bin/env python3
"""
训练行为克隆策略 - 修复导入路径版本
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import h5py
import os
import sys
import glob
from datetime import datetime
import matplotlib.pyplot as plt

# 修复导入路径 - 添加父目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

# 现在可以正常导入
from models.bc_network import BCPolicy, LSTMBCPolicy

class DemonstrationDataset(Dataset):
    """示教数据集"""
    def __init__(self, demo_dir):
        self.states = []
        self.actions = []
        
        # 查找所有.h5文件
        demo_files = sorted(glob.glob(os.path.join(demo_dir, '*.h5')))
        
        if len(demo_files) == 0:
            raise ValueError(f"No demonstration files found in {demo_dir}")
        
        print(f"Loading {len(demo_files)} demonstrations from {demo_dir}...")
        
        for demo_file in demo_files:
            try:
                with h5py.File(demo_file, 'r') as f:
                    positions = f['joint_positions'][:]
                    
                    # 状态：当前关节位置
                    # 动作：下一个关节位置（目标）
                    for i in range(len(positions) - 1):
                        self.states.append(positions[i])
                        self.actions.append(positions[i + 1])
                        
            except Exception as e:
                print(f"Warning: Failed to load {demo_file}: {e}")
                continue
        
        if len(self.states) == 0:
            raise ValueError("No valid data loaded from demonstrations")
        
        self.states = np.array(self.states, dtype=np.float32)
        self.actions = np.array(self.actions, dtype=np.float32)
        
        print(f"Loaded {len(self.states)} state-action pairs")
        print(f"State shape: {self.states.shape}")
        print(f"Action shape: {self.actions.shape}")
    
    def __len__(self):
        return len(self.states)
    
    def __getitem__(self, idx):
        state = torch.FloatTensor(self.states[idx])
        action = torch.FloatTensor(self.actions[idx])
        return state, action

def train_bc_policy(demo_dir, model_save_dir, 
                    epochs=100, batch_size=64, lr=1e-3,
                    use_lstm=False):
    """训练行为克隆策略"""
    
    print("=" * 60)
    print("Behavior Cloning Training")
    print("=" * 60)
    print(f"Demo directory: {demo_dir}")
    print(f"Model save directory: {model_save_dir}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Learning rate: {lr}")
    print(f"Use LSTM: {use_lstm}")
    print("=" * 60)
    print()
    
    # 确保模型保存目录存在
    os.makedirs(model_save_dir, exist_ok=True)
    
    # 加载数据
    dataset = DemonstrationDataset(demo_dir)
    
    # 划分训练集和验证集 (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, 
                            shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, 
                          shuffle=False, num_workers=2)
    
    print(f"Training samples: {train_size}")
    print(f"Validation samples: {val_size}")
    print()
    
    # 创建模型
    state_dim = 6  # UR5有6个关节
    action_dim = 6
    
    if use_lstm:
        model = LSTMBCPolicy(state_dim, action_dim)
        print("Using LSTM-based policy")
    else:
        model = BCPolicy(state_dim, action_dim)
        print("Using MLP-based policy")
    
    # 检查GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    model = model.to(device)
    print()
    
    # 优化器和损失函数
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    # 训练历史
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    
    print("Starting training...")
    print()
    
    # 训练循环
    for epoch in range(epochs):
        # 训练阶段
        model.train()
        train_loss = 0.0
        
        for states, actions in train_loader:
            states = states.to(device)
            actions = actions.to(device)
            
            # 前向传播
            pred_actions = model(states)
            loss = criterion(pred_actions, actions)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        train_losses.append(train_loss)
        
        # 验证阶段
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for states, actions in val_loader:
                states = states.to(device)
                actions = actions.to(device)
                
                pred_actions = model(states)
                loss = criterion(pred_actions, actions)
                
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        val_losses.append(val_loss)
        
        # 打印进度
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs}: "
                  f"Train Loss: {train_loss:.6f}, "
                  f"Val Loss: {val_loss:.6f}")
        
        # 保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            model_path = os.path.join(model_save_dir, 'bc_policy_best.pth')
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': train_loss,
                'val_loss': val_loss,
            }, model_path)
    
    print()
    print("=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Best validation loss: {best_val_loss:.6f}")
    print(f"Model saved to: {model_path}")
    print("=" * 60)
    print()
    
    # 绘制训练曲线
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Train Loss', linewidth=2)
    plt.plot(val_losses, label='Val Loss', linewidth=2)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Loss (MSE)', fontsize=12)
    plt.title('Training Curves', fontsize=14, fontweight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    curve_path = os.path.join(model_save_dir, 'training_curves.png')
    plt.savefig(curve_path, dpi=150)
    print(f"Training curves saved to: {curve_path}")
    print()
    
    return model, train_losses, val_losses

if __name__ == '__main__':
    # 设置路径（使用绝对路径）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ur5_imitation_dir = os.path.dirname(script_dir)
    
    demo_dir = os.path.join(ur5_imitation_dir, 'demonstrations')
    model_save_dir = os.path.join(ur5_imitation_dir, 'models')
    
    # 检查demonstrations目录
    if not os.path.exists(demo_dir):
        print(f"Error: Demonstrations directory not found: {demo_dir}")
        print("Please collect demonstrations first!")
        sys.exit(1)
    
    demo_files = glob.glob(os.path.join(demo_dir, '*.h5'))
    if len(demo_files) < 10:
        print(f"Warning: Only {len(demo_files)} demonstrations found")
        print("Recommended: at least 10-15 demonstrations for good performance")
        
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # 训练参数
    epochs = 100
    batch_size = 64
    learning_rate = 1e-3
    use_lstm = False  # 改为True使用LSTM
    
    # 训练
    try:
        model, train_losses, val_losses = train_bc_policy(
            demo_dir=demo_dir,
            model_save_dir=model_save_dir,
            epochs=epochs,
            batch_size=batch_size,
            lr=learning_rate,
            use_lstm=use_lstm
        )
        
        print("🎉 Training successful!")
        print()
        print("Next steps:")
        print("1. Review training curves:")
        print(f"   eog {model_save_dir}/training_curves.png")
        print()
        print("2. Test the policy:")
        print("   # Terminal 1")
        print("   roslaunch ur5_imitation ur5_gazebo.launch")
        print()
        print("   # Terminal 2")
        print(f"   rosrun ur5_imitation execute_policy.py {model_save_dir}/bc_policy_best.pth")
        print()
        
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
