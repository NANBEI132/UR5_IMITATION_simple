#!/bin/bash

# UR5模仿学习快速启动脚本

echo "=========================================="
echo "  UR5 Imitation Learning Quick Start"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查工作空间
if [ ! -f "devel/setup.bash" ]; then
    echo -e "${RED}错误: 请在工作空间根目录运行此脚本${NC}"
    exit 1
fi

# Source工作空间
source devel/setup.bash

# 主菜单
show_menu() {
    echo ""
    echo -e "${BLUE}请选择操作:${NC}"
    echo "1) 启动Gazebo仿真环境"
    echo "2) 数据采集 (使用主手控制器)"
    echo "3) 数据采集 (使用键盘控制)"
    echo "4) 训练策略网络"
    echo "5) 执行训练好的策略"
    echo "6) 评估策略性能"
    echo "7) 查看demonstrations"
    echo "8) 清理所有数据"
    echo "q) 退出"
    echo ""
}

# 启动Gazebo
start_gazebo() {
    echo -e "${GREEN}启动Gazebo仿真环境...${NC}"
    roslaunch ur5_imitation ur5_gazebo.launch
}

# 数据采集 - 主手
data_collection_leader() {
    echo -e "${GREEN}启动主手遥操作数据采集...${NC}"
    echo -e "${YELLOW}请确保主手控制器已连接并发布到 /leader/joint_states${NC}"
    read -p "按Enter继续..."
    roslaunch ur5_imitation data_collection.launch
}

# 数据采集 - 键盘
data_collection_keyboard() {
    echo -e "${GREEN}启动键盘控制数据采集...${NC}"
    echo ""
    echo "终端1: 启动Gazebo"
    echo "终端2: 启动键盘控制"
    echo "终端3: 启动数据记录"
    echo ""
    read -p "按Enter在此终端启动Gazebo..." 
    
    # 启动Gazebo
    gnome-terminal -- bash -c "source devel/setup.bash; roslaunch ur5_imitation ur5_gazebo.launch; exec bash"
    sleep 5
    
    # 启动键盘控制
    gnome-terminal -- bash -c "source devel/setup.bash; rosrun ur5_imitation keyboard_teleop.py; exec bash"
    sleep 2
    
    # 启动数据记录
    echo -e "${YELLOW}在数据记录终端中:${NC}"
    echo "  - 按 ENTER 开始记录"
    echo "  - 使用键盘控制机械臂完成任务"
    echo "  - 再按 ENTER 停止并保存"
    rosrun ur5_imitation data_recorder.py
}

# 训练策略
train_policy() {
    echo -e "${GREEN}训练策略网络...${NC}"
    
    # 检查demonstrations目录
    DEMO_DIR="src/ur5_imitation/demonstrations"
    if [ ! -d "$DEMO_DIR" ] || [ -z "$(ls -A $DEMO_DIR)" ]; then
        echo -e "${RED}错误: 未找到demonstration数据!${NC}"
        echo "请先使用选项2或3采集数据"
        return
    fi
    
    NUM_DEMOS=$(ls $DEMO_DIR/*.h5 2>/dev/null | wc -l)
    echo -e "${BLUE}找到 $NUM_DEMOS 个demonstrations${NC}"
    
    if [ $NUM_DEMOS -lt 5 ]; then
        echo -e "${YELLOW}警告: demonstrations数量较少，建议至少采集10个以上${NC}"
        read -p "是否继续训练? (y/n): " choice
        if [ "$choice" != "y" ]; then
            return
        fi
    fi
    
    # 开始训练
    cd src/ur5_imitation/scripts
    python3 train_policy.py
    cd ../../..
    
    echo -e "${GREEN}训练完成!${NC}"
}

# 执行策略
execute_policy() {
    echo -e "${GREEN}执行训练好的策略...${NC}"
    
    MODEL_PATH="src/ur5_imitation/models/bc_policy_best.pth"
    if [ ! -f "$MODEL_PATH" ]; then
        echo -e "${RED}错误: 未找到训练好的模型!${NC}"
        echo "请先使用选项4训练模型"
        return
    fi
    
    echo "终端1: 启动Gazebo"
    echo "终端2: 执行策略"
    read -p "按Enter继续..."
    
    # 启动Gazebo
    gnome-terminal -- bash -c "source devel/setup.bash; roslaunch ur5_imitation ur5_gazebo.launch; exec bash"
    sleep 5
    
    # 执行策略
    echo -e "${BLUE}正在执行策略...${NC}"
    rosrun ur5_imitation execute_policy.py $MODEL_PATH
}

# 评估策略
evaluate_policy() {
    echo -e "${GREEN}评估策略性能...${NC}"
    
    MODEL_PATH="src/ur5_imitation/models/bc_policy_best.pth"
    TEST_DATA_DIR="src/ur5_imitation/demonstrations"
    
    if [ ! -f "$MODEL_PATH" ]; then
        echo -e "${RED}错误: 未找到训练好的模型!${NC}"
        return
    fi
    
    cd src/ur5_imitation/scripts
    python3 evaluate_policy.py $MODEL_PATH $TEST_DATA_DIR --plot
    cd ../../..
    
    echo -e "${GREEN}评估完成! 查看生成的图表文件${NC}"
}

# 查看demonstrations
view_demonstrations() {
    DEMO_DIR="src/ur5_imitation/demonstrations"
    
    if [ ! -d "$DEMO_DIR" ]; then
        echo -e "${YELLOW}demonstrations目录不存在${NC}"
        return
    fi
    
    echo -e "${BLUE}Demonstrations:${NC}"
    ls -lh $DEMO_DIR/*.h5 2>/dev/null || echo "未找到demonstration文件"
    
    NUM_DEMOS=$(ls $DEMO_DIR/*.h5 2>/dev/null | wc -l)
    echo ""
    echo -e "${GREEN}总计: $NUM_DEMOS 个demonstrations${NC}"
}

# 清理数据
cleanup_data() {
    echo -e "${RED}警告: 这将删除所有demonstrations和训练好的模型!${NC}"
    read -p "确定要继续吗? (yes/no): " choice
    
    if [ "$choice" = "yes" ]; then
        rm -rf src/ur5_imitation/demonstrations/*.h5
        rm -rf src/ur5_imitation/models/*.pth
        rm -f *.png
        echo -e "${GREEN}清理完成${NC}"
    else
        echo "取消清理"
    fi
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项 [1-8/q]: " choice
    
    case $choice in
        1) start_gazebo ;;
        2) data_collection_leader ;;
        3) data_collection_keyboard ;;
        4) train_policy ;;
        5) execute_policy ;;
        6) evaluate_policy ;;
        7) view_demonstrations ;;
        8) cleanup_data ;;
        q|Q) 
            echo -e "${GREEN}再见!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项!${NC}"
            ;;
    esac
    
    echo ""
    read -p "按Enter继续..."
done
