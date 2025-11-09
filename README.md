# UR5 Python脚本修复包

## 🎯 这个包是什么？

根据你的`rostopic list`输出，你的UR5使用的是 **`eff_joint_traj_controller`** （力矩轨迹控制器），而原始代码假设使用位置控制器。

这个包包含了**自动适配你系统的修复版本**，会自动检测并使用正确的话题。

## 📦 包含文件

```
scripts_fix_package/
├── README.md                          ← 你在这里
├── TOPIC_FIX_GUIDE.md                 ← 详细修复指南
├── auto_fix.sh                        ← 一键自动替换脚本 ⭐
├── keyboard_teleop_fixed.py           ← 键盘控制（修复版）
├── data_recorder_fixed.py             ← 数据记录（修复版）
├── execute_policy_fixed.py            ← 策略执行（修复版）
└── leader_follower_teleop_fixed.py    ← 主从遥操作（修复版）
```

## 🚀 快速修复（1分钟）⭐

### 方法A：自动替换（最简单）

```bash
# 1. 进入修复包目录
cd scripts_fix_package

# 2. 给脚本执行权限
chmod +x auto_fix.sh

# 3. 运行自动修复
./auto_fix.sh

# 就这样！脚本会自动：
# - 备份原文件
# - 替换为修复版本
# - 设置权限
```

### 方法B：手动替换

```bash
# 进入目标目录
cd ~/ur5_imitation_ws/src/ur5_imitation/scripts

# 备份原文件
cp keyboard_teleop.py keyboard_teleop.py.backup
cp data_recorder.py data_recorder.py.backup
cp execute_policy.py execute_policy.py.backup
cp leader_follower_teleop.py leader_follower_teleop.py.backup

# 复制修复版本（假设修复包在 ~/Downloads/scripts_fix_package/）
cp ~/Downloads/scripts_fix_package/keyboard_teleop_fixed.py keyboard_teleop.py
cp ~/Downloads/scripts_fix_package/data_recorder_fixed.py data_recorder.py
cp ~/Downloads/scripts_fix_package/execute_policy_fixed.py execute_policy.py
cp ~/Downloads/scripts_fix_package/leader_follower_teleop_fixed.py leader_follower_teleop.py

# 设置权限
chmod +x *.py
```

## 🔍 修复了什么？

### 问题1：硬编码的话题名称
**原来：**
```python
self.command_pub = rospy.Publisher(
    '/ur5/joint_group_position_controller/command',  # 固定话题
    JointTrajectory,
    queue_size=1
)
```

**现在：**
```python
def detect_topics(self):
    """自动检测可用的话题"""
    topics = rospy.get_published_topics()
    topic_names = [t[0] for t in topics]
    
    # 优先使用你系统的控制器
    command_candidates = [
        '/eff_joint_traj_controller/command',      # 你的系统 ✓
        '/ur5/joint_group_position_controller/command',
        '/arm_controller/command'
    ]
    
    for candidate in command_candidates:
        if candidate in topic_names:
            self.command_topic = candidate
            break
```

### 问题2：缺少velocities字段
**原来：**
```python
point = JointTrajectoryPoint()
point.positions = action.tolist()
point.time_from_start = rospy.Duration(0.5)
# 缺少velocities字段
```

**现在：**
```python
point = JointTrajectoryPoint()
point.positions = action.tolist()
point.velocities = [0.0] * 6  # 力矩控制器需要
point.time_from_start = rospy.Duration(0.5)
```

## 📋 测试步骤

### 1️⃣ 测试键盘控制

```bash
# 终端1：启动Gazebo
roslaunch ur5_imitation ur5_gazebo.launch

# 终端2：键盘控制
rosrun ur5_imitation keyboard_teleop.py
```

**期望看到：**
```
Detecting available topics...
✓ Joint state topic: /ur5/joint_states
✓ Command topic: /eff_joint_traj_controller/command
Keyboard Teleoperation initialized
Ready! Start controlling with keyboard.
```

**测试操作：**
- 按 `Q` → 第一个关节正向转
- 按 `A` → 第一个关节负向转
- 按 `SPACE` → 回到零位
- 机械臂应该**平滑移动** ✅

### 2️⃣ 测试数据记录

```bash
# 终端3：数据记录
rosrun ur5_imitation data_recorder.py
```

**期望看到：**
```
Detecting joint state topic...
✓ Using topic: /ur5/joint_states
Demonstration Recorder initialized
```

**记录数据：**
```bash
# 终端4：开始记录
rosservice call /start_recording

# 使用键盘控制机械臂移动5-10秒

# 停止记录
rosservice call /stop_recording

# 检查保存的文件
ls ~/ur5_imitation_ws/src/ur5_imitation/demonstrations/
```

### 3️⃣ 完整流程测试

```bash
# 1. 采集10个demonstrations
for i in {1..10}; do
    echo "Recording demo $i..."
    rosservice call /start_recording
    # 手动操作机械臂
    sleep 10
    rosservice call /stop_recording
    sleep 2
done

# 2. 训练模型
cd ~/ur5_imitation_ws/src/ur5_imitation/scripts
python3 train_policy.py

# 3. 执行策略
rosrun ur5_imitation execute_policy.py ../models/bc_policy_best.pth
```

## ✅ 验证成功的标志

修复成功后，你应该看到：

### 键盘控制成功：
- ✅ 启动时显示检测到的话题
- ✅ 按键有响应
- ✅ 机械臂平滑移动（不抖动）
- ✅ 终端显示关节角度更新

### 数据记录成功：
- ✅ 能够开始/停止记录
- ✅ 成功保存.h5文件
- ✅ 文件大小合理（不为0KB）
- ✅ 能看到记录的样本数

### 检查命令：
```bash
# 检查demonstrations
ls -lh ~/ur5_imitation_ws/src/ur5_imitation/demonstrations/

# 应该看到类似：
# demo_20241029_120345.h5  (几KB到几百KB)

# 查看文件内容
python3 -c "
import h5py
with h5py.File('demonstrations/demo_*.h5', 'r') as f:
    print(f'Samples: {len(f[\"joint_positions\"])}')
    print(f'Duration: {f.attrs[\"duration\"]:.2f}s')
"
```

## 🔧 如果还有问题

### 问题1：找不到话题

```bash
# 检查Gazebo是否运行
rostopic list | grep joint

# 应该看到：
# /joint_states
# /ur5/joint_states

# 如果没有，重启Gazebo
```

### 问题2：控制器没响应

```bash
# 检查控制器状态
rosservice call /controller_manager/list_controllers

# 应该看到：
# eff_joint_traj_controller - running

# 如果stopped，手动启动：
rosservice call /controller_manager/switch_controller \
  "{start_controllers: ['eff_joint_traj_controller'], \
    stop_controllers: [], strictness: 2}"
```

### 问题3：机械臂抖动

如果机械臂移动时抖动，调整参数：

```python
# 在keyboard_teleop.py中修改
self.joint_step = 0.02  # 减小步长（原来0.05）
self.control_rate = 20  # 增加控制频率（原来10）
```

## 📚 详细文档

更多信息请阅读：
- **TOPIC_FIX_GUIDE.md** - 详细的修复说明和故障排除

## 🎯 你的系统配置

根据你的`rostopic list`，你的配置是：

| 功能 | 话题名称 |
|------|---------|
| 关节状态 | `/ur5/joint_states` |
| 控制器 | `/eff_joint_traj_controller/command` ✓ |
| 备用控制 | `/ur5/joint_group_position_controller/command` |

修复后的脚本会**自动检测并使用**这些话题！

## 💡 关键改进

1. **智能话题检测** - 自动适配不同系统
2. **完整消息格式** - 添加所有必需字段
3. **更好的日志** - 清晰显示使用的话题
4. **兼容性强** - 支持多种控制器类型

## 🔙 如何恢复原文件

如果需要恢复到修复前：

```bash
cd ~/ur5_imitation_ws/src/ur5_imitation/scripts

# 恢复原文件（auto_fix.sh会自动创建.backup）
mv keyboard_teleop.py.backup keyboard_teleop.py
mv data_recorder.py.backup data_recorder.py
mv execute_policy.py.backup execute_policy.py
mv leader_follower_teleop.py.backup leader_follower_teleop.py
```

## 📞 还需要帮助？

如果修复后还有问题，请运行这些命令并提供输出：

```bash
# 1. ROS版本
rosversion -d

# 2. 话题列表
rostopic list

# 3. 节点列表
rosnode list

# 4. 控制器状态
rosservice call /controller_manager/list_controllers

# 5. 关节数据
rostopic echo /ur5/joint_states -n 1
```

---

## 🚀 立即开始

```bash
# 最简单的方法：
cd scripts_fix_package
chmod +x auto_fix.sh
./auto_fix.sh

# 然后测试：
roslaunch ur5_imitation ur5_gazebo.launch
rosrun ur5_imitation keyboard_teleop.py
```

**修复只需1分钟，马上试试！** 💪

祝实验顺利！🎉
