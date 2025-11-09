# UR5模仿学习系统 - 详细安装指南

## 目录
1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [验证安装](#验证安装)
4. [常见问题](#常见问题)

## 系统要求

### 硬件要求
- CPU: Intel i5或更高（推荐i7以上）
- RAM: 8GB以上（推荐16GB）
- GPU: 可选，用于加速训练（NVIDIA显卡，支持CUDA）
- 存储: 至少20GB可用空间

### 软件要求
- **操作系统**: Ubuntu 20.04 LTS
- **ROS版本**: Noetic Ninjemys
- **Python版本**: 3.8或更高
- **PyTorch版本**: 1.9.0或更高

## 安装步骤

### 步骤1: 安装ROS Noetic

如果你还没有安装ROS Noetic，请按照以下步骤操作：

```bash
# 1. 设置sources.list
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'

# 2. 设置密钥
sudo apt install curl
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -

# 3. 更新软件源
sudo apt update

# 4. 安装ROS Noetic完整版
sudo apt install ros-noetic-desktop-full

# 5. 环境设置
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
source ~/.bashrc

# 6. 安装依赖工具
sudo apt install python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool build-essential

# 7. 初始化rosdep
sudo rosdep init
rosdep update
```

### 步骤2: 创建并配置工作空间

```bash
# 创建工作空间
mkdir -p ~/ur5_imitation_ws/src
cd ~/ur5_imitation_ws/src

# 初始化工作空间
cd ~/ur5_imitation_ws
catkin_make
source devel/setup.bash
```

### 步骤3: 安装UR机器人相关包

```bash
cd ~/ur5_imitation_ws/src

# 克隆universal_robot包
git clone -b noetic-devel https://github.com/ros-industrial/universal_robot.git

# 克隆fmauch版本（包含校准支持）
git clone -b calibration_devel https://github.com/fmauch/universal_robot.git fmauch_universal_robot

# 安装UR相关依赖
sudo apt-get install -y \
    ros-noetic-gazebo-ros-pkgs \
    ros-noetic-gazebo-ros-control \
    ros-noetic-ros-controllers \
    ros-noetic-joint-state-controller \
    ros-noetic-effort-controllers \
    ros-noetic-position-controllers \
    ros-noetic-joint-trajectory-controller \
    ros-noetic-controller-manager \
    ros-noetic-moveit \
    ros-noetic-moveit-visual-tools \
    ros-noetic-industrial-core
```

### 步骤4: 安装Python依赖

```bash
# 更新pip
pip3 install --upgrade pip

# 安装PyTorch（CPU版本）
pip3 install torch torchvision torchaudio

# 如果有NVIDIA GPU，安装CUDA版本（以CUDA 11.3为例）
# pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu113

# 安装其他依赖
pip3 install numpy matplotlib scipy scikit-learn pandas h5py opencv-python pyyaml tqdm
```

### 步骤5: 安装本项目

```bash
# 进入工作空间src目录
cd ~/ur5_imitation_ws/src

# 方法A: 如果有git仓库
# git clone <your_repository_url> ur5_imitation

# 方法B: 手动复制文件
# 将ur5_imitation_package文件夹复制到此处，并重命名为ur5_imitation
cp -r /path/to/ur5_imitation_package ./ur5_imitation

# 设置脚本权限
chmod +x ur5_imitation/scripts/*.py
chmod +x ur5_imitation/quick_start.sh
```

### 步骤6: 编译工作空间

```bash
cd ~/ur5_imitation_ws

# 安装依赖
rosdep install --from-paths src --ignore-src -r -y

# 编译
catkin_make

# Source工作空间
source devel/setup.bash

# 将source命令添加到bashrc（每次打开终端自动生效）
echo "source ~/ur5_imitation_ws/devel/setup.bash" >> ~/.bashrc
```

## 验证安装

### 1. 验证ROS安装

```bash
# 检查ROS版本
rosversion -d
# 应该输出: noetic

# 检查ROS环境变量
echo $ROS_DISTRO
# 应该输出: noetic
```

### 2. 验证UR包安装

```bash
# 检查ur_description包
rospack find ur_description

# 检查ur_gazebo包
rospack find ur_gazebo

# 如果没有错误，说明安装成功
```

### 3. 测试Gazebo仿真

```bash
# 启动Gazebo（首次启动可能较慢）
roslaunch ur5_imitation ur5_gazebo.launch

# 成功的标志：
# - Gazebo窗口打开
# - 可以看到UR5机械臂模型
# - 没有报错信息
```

### 4. 验证Python依赖

```bash
python3 -c "import torch; print('PyTorch version:', torch.__version__)"
python3 -c "import numpy; print('NumPy version:', numpy.__version__)"
python3 -c "import h5py; print('H5py version:', h5py.__version__)"
```

### 5. 测试完整流程

```bash
# 使用快速启动脚本
cd ~/ur5_imitation_ws
./src/ur5_imitation/quick_start.sh

# 选择选项1启动仿真
# 如果一切正常，Gazebo应该成功启动
```

## 常见问题

### 问题1: catkin_make失败

**症状**: 编译时出现CMake错误

**解决方案**:
```bash
# 清理并重新编译
cd ~/ur5_imitation_ws
catkin_make clean
rm -rf build/ devel/
catkin_make
```

### 问题2: 找不到ur_description包

**症状**: `rospack find ur_description` 报错

**解决方案**:
```bash
# 重新安装universal_robot包
cd ~/ur5_imitation_ws/src
rm -rf universal_robot
git clone -b noetic-devel https://github.com/ros-industrial/universal_robot.git
cd ..
catkin_make
```

### 问题3: Gazebo启动黑屏或崩溃

**症状**: Gazebo窗口打不开或者打开后崩溃

**解决方案**:
```bash
# 1. 更新显卡驱动（如果使用独立显卡）
# 2. 重置Gazebo配置
rm -rf ~/.gazebo

# 3. 尝试无GUI模式
roslaunch ur5_imitation ur5_gazebo.launch gui:=false
```

### 问题4: PyTorch安装失败

**症状**: pip安装PyTorch时出错

**解决方案**:
```bash
# 使用清华镜像
pip3 install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者使用conda（如果已安装）
conda install pytorch torchvision torchaudio cpuonly -c pytorch
```

### 问题5: 权限问题

**症状**: 无法执行脚本

**解决方案**:
```bash
# 添加执行权限
chmod +x ~/ur5_imitation_ws/src/ur5_imitation/scripts/*.py
chmod +x ~/ur5_imitation_ws/src/ur5_imitation/quick_start.sh
```

### 问题6: ROS话题收不到数据

**症状**: rostopic echo 没有输出

**解决方案**:
```bash
# 检查话题列表
rostopic list

# 检查节点
rosnode list

# 检查TF树
rosrun rqt_tf_tree rqt_tf_tree

# 重启节点
rosnode kill -a
# 然后重新启动launch文件
```

### 问题7: Gazebo中机械臂不响应控制

**症状**: 发送控制命令后机械臂不动

**解决方案**:
```bash
# 1. 检查控制器状态
rosservice call /controller_manager/list_controllers

# 2. 重启控制器
rosservice call /controller_manager/switch_controller "{start_controllers: ['joint_group_position_controller'], stop_controllers: [], strictness: 2, start_asap: false, timeout: 0.0}"

# 3. 手动加载控制器
rosrun controller_manager spawner joint_group_position_controller
```

## 性能优化建议

### 1. 加速Gazebo

在launch文件中添加：
```xml
<arg name="physics_engine" value="ode"/>
<arg name="extra_gazebo_args" value="--verbose"/>
```

### 2. GPU加速训练

安装CUDA版本的PyTorch，训练速度可提升5-10倍。

### 3. 减少数据记录频率

如果磁盘IO较慢，降低记录频率：
```python
self.record_frequency = 20  # 从50Hz降到20Hz
```

## 下一步

安装完成后，请参考以下文档：
- `README.md` - 快速开始指南
- `documentation/ur5_imitation_learning_guide.md` - 完整系统说明
- `config/training_config.yaml` - 训练配置说明

## 获取帮助

如果遇到其他问题：
1. 查看ROS官方文档: http://wiki.ros.org/noetic
2. 查看Universal Robots仓库的Issues
3. 提交Issue到本项目仓库

---

**祝安装顺利！**
