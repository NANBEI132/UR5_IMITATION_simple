import torch
import torch.nn as nn
import torch.nn.functional as F

class BCPolicy(nn.Module):
    """行为克隆策略网络"""
    
    def __init__(self, state_dim=6, action_dim=6, hidden_dims=[256, 256], 
                 use_vision=False, image_channels=3):
        super(BCPolicy, self).__init__()
        
        self.use_vision = use_vision
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # 视觉编码器（如果使用相机）
        if use_vision:
            self.vision_encoder = nn.Sequential(
                nn.Conv2d(image_channels, 32, kernel_size=8, stride=4),
                nn.ReLU(),
                nn.Conv2d(32, 64, kernel_size=4, stride=2),
                nn.ReLU(),
                nn.Conv2d(64, 64, kernel_size=3, stride=1),
                nn.ReLU(),
                nn.Flatten(),
                nn.Linear(64 * 7 * 7, 512),
                nn.ReLU()
            )
            mlp_input_dim = 512 + state_dim
        else:
            mlp_input_dim = state_dim
        
        # MLP策略网络
        layers = []
        prev_dim = mlp_input_dim
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, action_dim))
        self.policy_net = nn.Sequential(*layers)
        
    def forward(self, state, image=None):
        """
        Args:
            state: (batch, state_dim) - 当前关节位置
            image: (batch, C, H, W) - 可选的图像输入
        Returns:
            action: (batch, action_dim) - 预测的关节位置
        """
        if self.use_vision and image is not None:
            vision_features = self.vision_encoder(image)
            x = torch.cat([vision_features, state], dim=1)
        else:
            x = state
        
        action = self.policy_net(x)
        return action


class LSTMBCPolicy(nn.Module):
    """基于LSTM的序列策略（考虑时序信息）"""
    
    def __init__(self, state_dim=6, action_dim=6, hidden_dim=256, 
                 num_layers=2, sequence_length=10):
        super(LSTMBCPolicy, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.sequence_length = sequence_length
        
        # 状态编码
        self.state_encoder = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU()
        )
        
        # LSTM层
        self.lstm = nn.LSTM(
            input_size=128,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.1
        )
        
        # 输出层
        self.output_net = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )
    
    def forward(self, state_sequence):
        """
        Args:
            state_sequence: (batch, seq_len, state_dim)
        Returns:
            action: (batch, action_dim)
        """
        batch_size = state_sequence.size(0)
        
        # 编码每个时间步
        encoded = self.state_encoder(state_sequence)
        
        # LSTM处理
        lstm_out, (h_n, c_n) = self.lstm(encoded)
        
        # 使用最后一个时间步的输出
        last_output = lstm_out[:, -1, :]
        
        # 生成动作
        action = self.output_net(last_output)
        return action
