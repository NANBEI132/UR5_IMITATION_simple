# UR5 模仿学习系统 - 使用指南

> 🎯 **一句话说明：** 通过键盘演示机械臂动作 → 训练神经网络 → 机械臂自动执行

---

## 📋 目录

1. [快速开始](#快速开始)
2. [完整使用流程](#完整使用流程)
3. [常见问题](#常见问题)
4. [进阶扩展](#进阶扩展)
5. [最佳实践](#最佳实践)

---

## ⚡ 快速开始

### 系统要求

```bash
- Ubuntu 18.04/20.04
- ROS Melodic/Noetic
- Python 3.6+
- PyTorch 1.8+
- CUDA (推荐，用于GPU加速)
```
先有ur5相关的包：cd $HOME/catkin_ws/src

# retrieve the sources (replace '$ROS_DISTRO' with the ROS version you are using)
git clone -b $ROS_DISTRO-devel https://github.com/ros-industrial/universal_robot.git
，然后将本仓库的文件，克隆在和ur5包同一文件路径下，然后编译。
### 三步使用

```bash
# 步骤1：示教（收集15个演示）
roslaunch ur5_imitation data_collection.launch
# 按键盘控制，完成任务，按S保存

# 步骤2：训练（等待10分钟）
rosrun ur5_imitation train_policy.py

# 步骤3：执行（看机械臂自动完成任务）
rosrun ur5_imitation execute_policy.py \
  ~/ur5_imitation_ws/src/ur5_imitation/models/bc_policy_best.pth
```

---

## 📖 完整使用流程

### 阶段1️⃣：环境准备

#### 1.1 创建工作空间

```bash
# 创建ROS工作空间
mkdir -p ~/ur5_imitation_ws/src
cd ~/ur5_imitation_ws/src

# 克隆项目（或者复制你的项目文件夹）
git clone <your_repo_url> ur5_imitation

# 编译
cd ~/ur5_imitation_ws
catkin_make
source devel/setup.bash
```

#### 1.2 安装依赖

```bash
# ROS依赖
sudo apt-get install ros-$ROS_DISTRO-gazebo-ros-pkgs \
                     ros-$ROS_DISTRO-controller-manager \
                     ros-$ROS_DISTRO-joint-state-controller \
                     ros-$ROS_DISTRO-effort-controllers

# Python依赖
pip3 install torch torchvision h5py numpy matplotlib --break-system-packages
```

#### 1.3 验证安装

```bash
# 启动Gazebo测试
roslaunch ur5_imitation ur5_gazebo.launch

# 应该看到：
# ✓ Gazebo窗口打开
# ✓ UR5机械臂加载
# ✓ 无错误信息
```

---

### 阶段2️⃣：数据收集（示教）

#### 2.1 启动数据收集系统

```bash
# 终端1：启动仿真和数据记录
roslaunch ur5_imitation data_collection.launch

# 看到输出：
# ✓ Gazebo started
# ✓ Data recorder ready
# ✓ Press 'S' to start/stop recording
```

#### 2.2 执行示教

**控制方式：**

| 按键 | 功能 |
|------|------|
| `W/S` | 关节1 +/- |
| `A/D` | 关节2 +/- |
| `Q/E` | 关节3 +/- |
| `R/F` | 关节4 +/- |
| `T/G` | 关节5 +/- |
| `Y/H` | 关节6 +/- |
| `Space` | 紧急停止 |
| **`S`** | **开始/停止录制** |

**示教步骤：**

```bash
# 1. 移动机械臂到起始位置
# 2. 按 S 开始录制
# 3. 控制机械臂完成任务（例如：抓取、移动、放置）
# 4. 按 S 停止录制
# 5. 文件自动保存到 demonstrations/demo_YYYYMMDD_HHMMSS.h5

# 重复15次（每次可以从不同起始位置开始）
```

#### 2.3 示教建议

**好的示教：** ✅
- 每次演示5-10秒
- 动作连贯、流畅
- 从不同起始位置开始
- 完成相同的最终目标
- 总共15-20个演示

**避免：** ❌
- 动作太快（机械臂跟不上）
- 动作太慢（数据冗余）
- 中途停顿太久
- 每次做不同的任务

#### 2.4 验证数据

```bash
# 查看收集的演示
ls ~/ur5_imitation_ws/src/ur5_imitation/demonstrations/

# 应该看到：
# demo_20241029_143052.h5
# demo_20241029_143127.h5
# ...
# demo_20241029_143856.h5  (共15个文件)

# 检查数据质量
python3 ~/ur5_imitation_ws/src/ur5_imitation/scripts/visualize_data.py
```

---

### 阶段3️⃣：训练策略

#### 3.1 开始训练

```bash
# 关闭Gazebo（节省资源）
Ctrl+C in terminal 1

# 启动训练
cd ~/ur5_imitation_ws/src/ur5_imitation/scripts
python3 train_policy.py

# 或者使用rosrun
rosrun ur5_imitation train_policy.py
```

#### 3.2 监控训练

**正常输出：**
```
============================================================
Training BC Policy
============================================================
Loading demonstrations from: ../demonstrations
Found 15 demonstration files
Total samples: 3750

Epoch [1/100]: Train Loss: 0.1234, Val Loss: 0.0987
Epoch [10/100]: Train Loss: 0.0234, Val Loss: 0.0187
Epoch [50/100]: Train Loss: 0.0045, Val Loss: 0.0039  ← 开始收敛
Epoch [100/100]: Train Loss: 0.0023, Val Loss: 0.0019  ← 训练完成！

✓ Best model saved to: ../models/bc_policy_best.pth
Training completed!
```

**训练时间：**
- CPU：约30-60分钟
- GPU：约5-15分钟

**判断训练质量：**
```
优秀：Val Loss < 0.005  ✅
良好：Val Loss < 0.01   ✅
一般：Val Loss < 0.05   ⚠️
差：  Val Loss > 0.05   ❌ 需要重新收集数据
```

#### 3.3 查看训练曲线

```bash
# 生成训练曲线图
python3 visualize_training.py

# 打开图片
eog training_curves.png
```

---

### 阶段4️⃣：执行策略

#### 4.1 启动仿真环境

```bash
# 终端1：启动Gazebo
roslaunch ur5_imitation ur5_gazebo.launch

# 等待Gazebo完全加载
```

#### 4.2 执行策略

```bash
# 终端2：运行策略
rosrun ur5_imitation execute_policy.py \
  ~/ur5_imitation_ws/src/ur5_imitation/models/bc_policy_best.pth

# 或者使用绝对路径
python3 ~/ur5_imitation_ws/src/ur5_imitation/scripts/execute_policy.py \
  ~/ur5_imitation_ws/src/ur5_imitation/models/bc_policy_best.pth
```

#### 4.3 观察执行

**成功标志：** ✅
```
- 机械臂流畅地移动
- 重复你示教的动作
- 动作连贯、不抖动
- 能够完成任务目标

终端输出：
Step   20: Current: [-0.380, +0.202, -0.013, ...], Target: [...], Max diff: 0.0052
Step   40: Current: [-0.382, +0.200, -0.012, ...], Target: [...], Max diff: 0.0045
```

**失败标志：** ❌
```
- 机械臂不动
- 动作抖动、不连贯
- 偏离预期轨迹
- 无法完成任务

解决方法：
1. 检查控制器话题（参考故障排查）
2. 重新训练
3. 收集更多高质量演示
```

---

## 🔧 常见问题

### Q1: 机械臂不动

**诊断：**
```bash
# 运行诊断工具
python3 diagnose_topics.py

# 检查控制器
rosservice call /controller_manager/list_controllers

# 手动测试控制
rostopic pub /eff_joint_traj_controller/command trajectory_msgs/JointTrajectory \
"header:
  seq: 0
  stamp: {secs: 0, nsecs: 0}
  frame_id: ''
joint_names: ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
              'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
points:
- positions: [0.0, -0.5, 0.5, 0.0, 0.0, 0.0]
  velocities: []
  accelerations: []
  effort: []
  time_from_start: {secs: 1, nsecs: 0}" -1
```

**解决方案：**
```bash
# 使用正确版本的execute_policy.py
cp execute_policy_eff_traj.py execute_policy.py

# 确保使用正确的话题：
# /eff_joint_traj_controller/command
```

### Q2: 训练Loss不下降

**可能原因：**
1. 数据质量差
2. 数据量太少
3. 学习率不合适

**解决方案：**
```bash
# 1. 检查数据
python3 visualize_data.py

# 2. 收集更多演示（至少15个）

# 3. 调整学习率
# 编辑train_policy.py
optimizer = optim.Adam(policy.parameters(), lr=0.0001)  # 降低学习率
```

### Q3: Gazebo启动失败

**解决方案：**
```bash
# 检查Gazebo版本
gazebo --version

# 清理Gazebo缓存
rm -rf ~/.gazebo/

# 重新启动
roslaunch ur5_imitation ur5_gazebo.launch
```

### Q4: 导入模块错误

**解决方案：**
```bash
# 确保路径正确
export PYTHONPATH=$PYTHONPATH:~/ur5_imitation_ws/src/ur5_imitation

# 或者在脚本中添加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

---

## 🚀 进阶扩展

### 扩展1：使用遥控设备进行数据收集

#### 为什么需要遥控设备？

**键盘控制的局限：** ❌
- 一次只能控制一个关节
- 动作不够流畅
- 难以完成复杂轨迹
- 收集数据效率低

**遥控设备的优势：** ✅
- 多轴同时控制
- 动作更自然流畅
- 类似真实操作体验
- 数据质量更高

---

### 方案A：SpaceMouse 3D鼠标 ⭐⭐⭐⭐⭐

**推荐型号：**
- SpaceMouse Wireless
- SpaceMouse Compact
- SpaceMouse Pro

**优点：**
- 6自由度控制（X/Y/Z移动 + Roll/Pitch/Yaw旋转）
- 专业设备，精度高
- ROS官方支持好

#### 安装步骤

```bash
# 1. 安装驱动
sudo apt-get install spacenavd
sudo systemctl start spacenavd
sudo systemctl enable spacenavd

# 2. 安装ROS包
sudo apt-get install ros-$ROS_DISTRO-spacenav-node

# 3. 测试连接
rostopic echo /spacenav/joy

# 应该看到数据输出（移动SpaceMouse时）
```

#### 创建SpaceMouse遥控脚本

```bash
# 创建文件：spacemouse_teleop.py
```

<details>
<summary>点击查看完整代码</summary>

```python
#!/usr/bin/env python3
"""
SpaceMouse遥控控制 - 更流畅的数据收集
"""
import rospy
from sensor_msgs.msg import Joy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import numpy as np

class SpaceMouseTeleop:
    def __init__(self):
        rospy.init_node('spacemouse_teleop')
        
        # 当前关节位置
        self.current_joints = np.zeros(6)
        
        # 控制参数
        self.translation_scale = 0.1  # 平移缩放
        self.rotation_scale = 0.1     # 旋转缩放
        
        # 订阅SpaceMouse
        self.spacenav_sub = rospy.Subscriber(
            '/spacenav/joy',
            Joy,
            self.spacenav_callback
        )
        
        # 发布命令
        self.cmd_pub = rospy.Publisher(
            '/eff_joint_traj_controller/command',
            JointTrajectory,
            queue_size=1
        )
        
        self.rate = rospy.Rate(50)
        
        print("SpaceMouse Teleop Ready!")
        print("Move the SpaceMouse to control the robot")
        
    def spacenav_callback(self, msg):
        """处理SpaceMouse输入"""
        # msg.axes[0-2]: X, Y, Z平移
        # msg.axes[3-5]: Roll, Pitch, Yaw旋转
        
        # 简化映射：直接控制前6个关节
        delta = np.array([
            msg.axes[0] * self.translation_scale,   # 关节1
            msg.axes[1] * self.translation_scale,   # 关节2
            msg.axes[2] * self.translation_scale,   # 关节3
            msg.axes[3] * self.rotation_scale,      # 关节4
            msg.axes[4] * self.rotation_scale,      # 关节5
            msg.axes[5] * self.rotation_scale       # 关节6
        ])
        
        # 更新目标位置
        self.current_joints += delta * 0.01
        
        # 限制范围
        self.current_joints = np.clip(self.current_joints, -2*np.pi, 2*np.pi)
        
        # 发送命令
        self.send_command(self.current_joints)
    
    def send_command(self, positions):
        """发送关节命令"""
        msg = JointTrajectory()
        msg.header.stamp = rospy.Time.now()
        msg.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]
        
        point = JointTrajectoryPoint()
        point.positions = positions.tolist()
        point.time_from_start = rospy.Duration(0.02)
        
        msg.points = [point]
        self.cmd_pub.publish(msg)
    
    def run(self):
        """主循环"""
        rospy.spin()

if __name__ == '__main__':
    try:
        teleop = SpaceMouseTeleop()
        teleop.run()
    except rospy.ROSInterruptException:
        pass
```
</details>

#### 使用方法

```bash
# 终端1：启动Gazebo
roslaunch ur5_imitation ur5_gazebo.launch

# 终端2：启动SpaceMouse节点
rosrun spacenav_node spacenav_node

# 终端3：启动遥控控制
python3 spacemouse_teleop.py

# 终端4：启动数据记录（当准备好时）
python3 data_recorder.py
```

---

### 方案B：游戏手柄 ⭐⭐⭐⭐

**推荐型号：**
- Xbox One/Series 手柄
- PlayStation 4/5 手柄
- Logitech F310

**优点：**
- 价格便宜（100-300元）
- 容易获取
- 多按钮、多摇杆

#### 安装步骤

```bash
# 1. 连接手柄（USB或蓝牙）

# 2. 测试连接
sudo apt-get install jstest-gtk
jstest /dev/input/js0

# 3. 安装ROS joy包
sudo apt-get install ros-$ROS_DISTRO-joy

# 4. 启动joy节点
rosrun joy joy_node

# 5. 测试数据
rostopic echo /joy
```

#### 创建手柄遥控脚本

```bash
# 创建文件：gamepad_teleop.py
```

<details>
<summary>点击查看完整代码</summary>

```python
#!/usr/bin/env python3
"""
游戏手柄遥控控制
Xbox布局：
  左摇杆：控制关节1、2
  右摇杆：控制关节3、4
  L1/R1: 控制关节5
  L2/R2: 控制关节6
  A按钮：开始/停止录制
"""
import rospy
from sensor_msgs.msg import Joy, JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import numpy as np

class GamepadTeleop:
    def __init__(self):
        rospy.init_node('gamepad_teleop')
        
        # 当前关节位置
        self.current_joints = np.zeros(6)
        self.joint_received = False
        
        # 控制参数
        self.velocity_scale = 0.5
        
        # 订阅关节状态
        self.joint_sub = rospy.Subscriber(
            '/joint_states',
            JointState,
            self.joint_callback
        )
        
        # 订阅手柄
        self.joy_sub = rospy.Subscriber(
            '/joy',
            Joy,
            self.joy_callback
        )
        
        # 发布命令
        self.cmd_pub = rospy.Publisher(
            '/eff_joint_traj_controller/command',
            JointTrajectory,
            queue_size=1
        )
        
        self.rate = rospy.Rate(50)
        
        print("=" * 60)
        print("Gamepad Teleop Ready!")
        print("=" * 60)
        print("Controls (Xbox layout):")
        print("  Left Stick:  Joint 1 & 2")
        print("  Right Stick: Joint 3 & 4")
        print("  LB/RB:       Joint 5")
        print("  LT/RT:       Joint 6")
        print("  A Button:    Start/Stop Recording")
        print("=" * 60)
        
    def joint_callback(self, msg):
        """获取当前关节位置"""
        if len(msg.position) >= 6:
            self.current_joints = np.array(msg.position[:6])
            self.joint_received = True
    
    def joy_callback(self, msg):
        """处理手柄输入"""
        if not self.joint_received:
            return
        
        # Xbox手柄映射（可能需要根据实际调整）
        # axes[0]: 左摇杆X
        # axes[1]: 左摇杆Y
        # axes[2]: LT (左扳机)
        # axes[3]: 右摇杆X
        # axes[4]: 右摇杆Y
        # axes[5]: RT (右扳机)
        # buttons[4]: LB
        # buttons[5]: RB
        
        # 计算速度增量
        dt = 1.0 / 50.0  # 50Hz
        
        velocity = np.zeros(6)
        velocity[0] = msg.axes[0] * self.velocity_scale  # 左摇杆X → 关节1
        velocity[1] = msg.axes[1] * self.velocity_scale  # 左摇杆Y → 关节2
        velocity[2] = msg.axes[4] * self.velocity_scale  # 右摇杆Y → 关节3
        velocity[3] = msg.axes[3] * self.velocity_scale  # 右摇杆X → 关节4
        
        # LB/RB控制关节5
        if len(msg.buttons) > 5:
            if msg.buttons[4]:  # LB
                velocity[4] = -self.velocity_scale
            elif msg.buttons[5]:  # RB
                velocity[4] = self.velocity_scale
        
        # LT/RT控制关节6
        if len(msg.axes) > 5:
            velocity[5] = (msg.axes[2] - msg.axes[5]) * self.velocity_scale
        
        # 更新目标位置
        target_joints = self.current_joints + velocity * dt
        
        # 限制范围
        target_joints = np.clip(target_joints, -2*np.pi, 2*np.pi)
        
        # 发送命令
        self.send_command(target_joints)
    
    def send_command(self, positions):
        """发送关节命令"""
        msg = JointTrajectory()
        msg.header.stamp = rospy.Time.now()
        msg.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]
        
        point = JointTrajectoryPoint()
        point.positions = positions.tolist()
        point.time_from_start = rospy.Duration(0.02)
        
        msg.points = [point]
        self.cmd_pub.publish(msg)
    
    def run(self):
        """主循环"""
        rospy.spin()

if __name__ == '__main__':
    try:
        teleop = GamepadTeleop()
        teleop.run()
    except rospy.ROSInterruptException:
        pass
```
</details>

#### 使用方法

```bash
# 终端1：Gazebo
roslaunch ur5_imitation ur5_gazebo.launch

# 终端2：Joy节点
rosrun joy joy_node

# 终端3：手柄遥控
python3 gamepad_teleop.py

# 终端4：数据记录
python3 data_recorder.py
# 在手柄遥控时按A键开始/停止录制
```

---

### 方案C：VR控制器 ⭐⭐⭐⭐⭐

**适合：** 有VR设备的用户（Oculus Quest、HTC Vive等）

**优点：**
- 最直观的控制方式
- 6自由度空间定位
- 沉浸式体验

**需要的包：**
```bash
# 安装VR ROS包
sudo apt-get install ros-$ROS_DISTRO-vrpn-client-ros

# 配置VR设备与ROS通信
```

---

### 扩展2：使用真实机械臂

#### 从仿真到真实的迁移

**步骤：**

```bash
# 1. 在仿真中训练策略
roslaunch ur5_imitation data_collection.launch  # Gazebo
python3 train_policy.py

# 2. 连接真实机械臂
# 编辑launch文件，指向真实机器人IP

# 3. 测试连接
roslaunch ur_robot_driver ur5_bringup.launch robot_ip:=192.168.1.100

# 4. 小心执行（先降低速度）
python3 execute_policy.py bc_policy_best.pth
```

**注意事项：** ⚠️
- 先在仿真中充分测试
- 真实机械臂设置速度限制
- 准备紧急停止按钮
- 确保工作空间安全
- 考虑Sim-to-Real差异

---

### 扩展3：多模态输入

#### 添加视觉输入

```python
# 修改网络以接受图像
class VisionBCPolicy(nn.Module):
    def __init__(self):
        # CNN处理图像
        self.vision_encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2),
            nn.ReLU(),
            nn.Flatten()
        )
        
        # 结合关节状态
        self.policy = nn.Sequential(
            nn.Linear(64*55*55 + 6, 256),
            nn.ReLU(),
            nn.Linear(256, 6)
        )
```

---

## 💡 最佳实践

### 数据收集

**DO：** ✅
1. 每次演示5-10秒
2. 动作流畅连贯
3. 从不同起始位置开始
4. 保持任务目标一致
5. 至少15个高质量演示

**DON'T：** ❌
1. 动作太快或太慢
2. 中途长时间停顿
3. 每次做不同任务
4. 示教数量太少（<10个）

### 训练

**DO：** ✅
1. 监控训练曲线
2. 使用验证集
3. 保存最佳模型
4. 尝试不同超参数

**DON'T：** ❌
1. 过度训练（过拟合）
2. 忽略验证Loss
3. 数据质量差就强行训练

### 执行

**DO：** ✅
1. 先在仿真中测试
2. 观察执行质量
3. 记录失败案例
4. 迭代改进

**DON'T：** ❌
1. 直接在真实机器人上执行未测试的策略
2. 忽略安全问题

---

## 📊 性能指标

### 评估标准

```bash
数据质量：
  ✓ 至少15个演示
  ✓ 每个演示200+样本
  ✓ 演示一致性高

训练质量：
  ✓ Val Loss < 0.01
  ✓ 训练曲线收敛
  ✓ 无明显过拟合

执行质量：
  ✓ 成功率 > 80%
  ✓ 动作流畅
  ✓ 完成任务目标
```

---

## 🔗 资源链接

### 项目文件

```
ur5_imitation/
├── scripts/
│   ├── data_recorder.py         # 数据记录
│   ├── keyboard_teleop.py       # 键盘控制
│   ├── train_policy.py          # 训练脚本
│   ├── execute_policy.py        # 执行脚本
│   ├── spacemouse_teleop.py     # SpaceMouse控制（扩展）
│   └── gamepad_teleop.py        # 手柄控制（扩展）
├── models/
│   └── bc_network.py            # 网络定义
├── demonstrations/              # 演示数据
├── models/                      # 保存的模型
└── launch/
    ├── ur5_gazebo.launch
    └── data_collection.launch
```

### 相关文档

- [完整原理解释](IMITATION_LEARNING_EXPLAINED.md)
- [简化理解版](SIMPLE_EXPLANATION.md)
- [故障诊断工具](diagnose_topics.py)

---

## 📞 故障排查速查表

| 问题 | 快速解决 |
|------|---------|
| Gazebo启动失败 | `rm -rf ~/.gazebo/` |
| 机械臂不动 | 检查话题：`python3 diagnose_topics.py` |
| 训练Loss不下降 | 检查数据质量、增加演示数量 |
| 导入错误 | `export PYTHONPATH=...` |
| 控制器错误 | 使用`execute_policy_eff_traj.py` |
| 手柄无响应 | `jstest /dev/input/js0` |

---

## 🎯 快速参考命令

```bash
# 数据收集
roslaunch ur5_imitation data_collection.launch

# 训练
python3 train_policy.py

# 执行
rosrun ur5_imitation execute_policy.py models/bc_policy_best.pth

# 诊断
python3 diagnose_topics.py

# 查看数据
ls demonstrations/

# 查看模型
ls models/
```

---

## 📈 改进路线图

### 短期（1周内）
- [ ] 收集高质量演示
- [ ] 训练基础策略
- [ ] 在仿真中验证

### 中期（1月内）
- [ ] 添加手柄/SpaceMouse支持
- [ ] 收集更多样化数据
- [ ] 优化网络结构

### 长期（3月+）
- [ ] 添加视觉输入
- [ ] 迁移到真实机器人
- [ ] 多任务学习

---


