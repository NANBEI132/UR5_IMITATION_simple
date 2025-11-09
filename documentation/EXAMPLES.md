# UR5模仿学习 - 使用示例

本文档提供具体的使用场景和示例。

## 📋 目录

1. [场景1: 简单抓取任务](#场景1-简单抓取任务)
2. [场景2: 轨迹跟踪](#场景2-轨迹跟踪)
3. [场景3: 多技能学习](#场景3-多技能学习)
4. [高级技巧](#高级技巧)

---

## 场景1: 简单抓取任务

### 任务描述
训练UR5机械臂从桌面抓取物体并放置到指定位置。

### 步骤

#### 1. 环境准备

```bash
# 终端1: 启动Gazebo（添加桌面和物体）
roslaunch ur5_imitation ur5_gazebo.launch
```

#### 2. 数据采集

采集10-20个成功的抓取demonstrations：

```bash
# 终端1: 启动键盘控制
rosrun ur5_imitation keyboard_teleop.py

# 终端2: 启动数据记录
rosrun ur5_imitation data_recorder.py
```

**示教要点**:
- 保持动作平滑，避免急停急起
- 每个demonstration应该完成完整的抓取-放置流程
- 尝试不同的起始位置以提高泛化性

#### 3. 训练策略

```bash
cd ~/ur5_imitation_ws/src/ur5_imitation/scripts

# 使用默认配置训练
python3 train_policy.py
```

预期训练时间：5-10分钟（取决于CPU/GPU）

#### 4. 评估和部署

```bash
# 评估
python3 evaluate_policy.py ../models/bc_policy_best.pth ../demonstrations --plot

# 如果MAE < 0.05 rad，可以进行部署
# 执行策略
rosrun ur5_imitation execute_policy.py ../models/bc_policy_best.pth
```

### 预期结果

- 训练损失应该下降到 < 0.01
- 每个关节的MAE应该 < 0.05 rad (约3度)
- 成功率应该 > 80%

---

## 场景2: 轨迹跟踪

### 任务描述
让机械臂学习跟踪一个圆形轨迹。

### 数据采集策略

使用主手控制器缓慢地引导机械臂完成圆形运动：

```bash
# 1. 启动系统
roslaunch ur5_imitation data_collection.launch

# 2. 记录多个完整的圆形轨迹（至少15个）
# 建议：
# - 顺时针和逆时针各一半
# - 不同的起始点
# - 不同的圆周大小
```

### 训练配置

修改`train_policy.py`中的配置：

```python
config = {
    'demo_dir': './demonstrations',
    'save_path': './models/circle_tracking.pth',
    'batch_size': 128,          # 增大batch size
    'num_epochs': 300,          # 增加训练轮数
    'learning_rate': 5e-4,      # 降低学习率
    'sequence_length': 15,      # 使用LSTM，序列长度15
    'use_velocity': False,
    'hidden_dim': 512,          # 增大网络容量
}
```

### 训练和评估

```bash
# 训练
python3 train_policy.py

# 可视化轨迹
python3 evaluate_policy.py ../models/circle_tracking.pth ../demonstrations --plot --demo-idx 0
```

### 性能指标

对于轨迹跟踪任务：
- MSE应该 < 0.001
- 轨迹的圆度误差应该 < 5%
- 速度应该平滑，无突变

---

## 场景3: 多技能学习

### 任务描述
训练机械臂掌握多个不同的技能（如抓取、放置、推动等）

### 数据组织

```
demonstrations/
├── skill_pick/
│   ├── demo_001.h5
│   ├── demo_002.h5
│   └── ...
├── skill_place/
│   ├── demo_001.h5
│   └── ...
└── skill_push/
    ├── demo_001.h5
    └── ...
```

### 修改数据加载器

在`train_policy.py`中：

```python
class MultiSkillDataset(Dataset):
    def __init__(self, skill_dirs, sequence_length=1):
        self.states = []
        self.actions = []
        self.skills = []  # 技能标签
        
        for skill_id, skill_dir in enumerate(skill_dirs):
            demo_files = glob.glob(os.path.join(skill_dir, '*.h5'))
            for demo_file in demo_files:
                with h5py.File(demo_file, 'r') as f:
                    joint_positions = f['joint_positions'][:]
                    states = joint_positions[:-1]
                    actions = joint_positions[1:]
                    
                    self.states.append(states)
                    self.actions.append(actions)
                    # 添加技能one-hot编码
                    skill_labels = np.ones((len(states), 1)) * skill_id
                    self.skills.append(skill_labels)
        
        self.states = np.concatenate(self.states, axis=0)
        self.actions = np.concatenate(self.actions, axis=0)
        self.skills = np.concatenate(self.skills, axis=0)
```

### 修改网络结构

```python
class MultiSkillPolicy(nn.Module):
    def __init__(self, state_dim=6, action_dim=6, num_skills=3, hidden_dims=[256, 256]):
        super().__init__()
        
        # 技能嵌入
        self.skill_embedding = nn.Embedding(num_skills, 64)
        
        # 策略网络
        self.policy_net = nn.Sequential(
            nn.Linear(state_dim + 64, hidden_dims[0]),
            nn.ReLU(),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
            nn.Linear(hidden_dims[1], action_dim)
        )
    
    def forward(self, state, skill_id):
        skill_emb = self.skill_embedding(skill_id)
        x = torch.cat([state, skill_emb], dim=1)
        return self.policy_net(x)
```

---

## 高级技巧

### 1. 数据增强

添加噪声提高鲁棒性：

```python
def augment_data(state, action):
    # 关节位置噪声
    if np.random.rand() < 0.3:
        state += np.random.normal(0, 0.01, state.shape)
    
    # 时间扭曲
    if np.random.rand() < 0.2:
        # 随机加速或减速
        pass
    
    return state, action
```

### 2. DAgger算法

交互式学习，提高策略性能：

```python
# 在execute_policy.py中添加
class DAggerCollector:
    def __init__(self, model, expert_controller):
        self.model = model
        self.expert = expert_controller
        self.beta = 1.0  # 专家混合比例
        
    def collect_data(self):
        state = get_current_state()
        
        # 以概率beta使用专家动作
        if np.random.rand() < self.beta:
            action = self.expert.get_action(state)
        else:
            action = self.model.predict(state)
        
        # 记录（state, expert_action）对
        self.save(state, self.expert.get_action(state))
        
        # 逐渐减少专家干预
        self.beta *= 0.99
        
        return action
```

### 3. 使用预训练模型

迁移学习加速训练：

```python
# 加载预训练模型
pretrained = torch.load('pretrained_model.pth')
model.load_state_dict(pretrained['model_state_dict'], strict=False)

# 冻结早期层
for param in model.policy_net[:2].parameters():
    param.requires_grad = False

# 只训练后面的层
optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4)
```

### 4. 添加约束和安全层

```python
class SafetyWrapper:
    def __init__(self, policy, joint_limits):
        self.policy = policy
        self.joint_limits = joint_limits
        
    def predict(self, state):
        action = self.policy(state)
        
        # 限制关节范围
        for i, (min_val, max_val) in enumerate(self.joint_limits):
            action[i] = np.clip(action[i], min_val, max_val)
        
        # 限制速度
        velocity = action - state
        max_velocity = 0.1  # rad/s
        velocity = np.clip(velocity, -max_velocity, max_velocity)
        action = state + velocity
        
        return action
```

### 5. 在线学习和适应

```python
# 在执行过程中持续学习
class OnlineLearner:
    def __init__(self, model, optimizer):
        self.model = model
        self.optimizer = optimizer
        self.buffer = []
        
    def execute_and_learn(self, state):
        # 执行
        action = self.model.predict(state)
        
        # 获取反馈（例如任务成功/失败）
        reward = execute_action(action)
        
        # 如果失败，让专家示教正确动作
        if reward < threshold:
            correct_action = get_expert_correction()
            self.buffer.append((state, correct_action))
            
            # 在线更新
            if len(self.buffer) > batch_size:
                self.update_model()
```

---

## 调试技巧

### 1. 可视化demonstrations

```python
import matplotlib.pyplot as plt
import h5py

def visualize_demo(demo_file):
    with h5py.File(demo_file, 'r') as f:
        joints = f['joint_positions'][:]
        
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    joint_names = ['Shoulder Pan', 'Shoulder Lift', 'Elbow', 
                   'Wrist 1', 'Wrist 2', 'Wrist 3']
    
    for i, (ax, name) in enumerate(zip(axes.flatten(), joint_names)):
        ax.plot(joints[:, i])
        ax.set_title(name)
        ax.set_xlabel('Timestep')
        ax.set_ylabel('Position (rad)')
        ax.grid(True)
    
    plt.tight_layout()
    plt.show()

# 使用
visualize_demo('demonstrations/demo_001.h5')
```

### 2. 监控训练过程

```python
# 在train_policy.py中添加
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter('runs/experiment_1')

for epoch in range(num_epochs):
    # ... 训练代码 ...
    
    writer.add_scalar('Loss/train', train_loss, epoch)
    writer.add_scalar('Loss/val', val_loss, epoch)
    writer.add_scalar('Learning_rate', optimizer.param_groups[0]['lr'], epoch)

# 启动tensorboard
# tensorboard --logdir=runs
```

### 3. 检查数据质量

```python
def check_data_quality(demo_files):
    for demo_file in demo_files:
        with h5py.File(demo_file, 'r') as f:
            joints = f['joint_positions'][:]
            
            # 检查轨迹平滑度
            velocities = np.diff(joints, axis=0)
            accelerations = np.diff(velocities, axis=0)
            
            max_vel = np.max(np.abs(velocities))
            max_acc = np.max(np.abs(accelerations))
            
            print(f"{demo_file}:")
            print(f"  Max velocity: {max_vel:.3f} rad/step")
            print(f"  Max acceleration: {max_acc:.3f} rad/step^2")
            
            if max_vel > 0.1 or max_acc > 0.05:
                print(f"  ⚠️  Warning: Trajectory may be too jerky!")
```

---

## 性能优化检查清单

- [ ] 采集足够的demonstrations（至少10个）
- [ ] demonstrations覆盖不同的起始状态
- [ ] 轨迹平滑，无突变
- [ ] 训练损失稳定下降
- [ ] 验证损失不发散（无过拟合）
- [ ] 每个关节的误差均匀（无单个关节误差过大）
- [ ] 执行时机械臂动作流畅
- [ ] 任务成功率达标

---

## 下一步扩展

1. **添加视觉感知**: 集成相机，基于视觉的策略
2. **力控制**: 添加力传感器，学习接触任务
3. **动态环境**: 处理移动物体
4. **多机器人协作**: 双臂协同操作
5. **强化学习结合**: BC + RL微调

---

**持续改进你的系统！**
