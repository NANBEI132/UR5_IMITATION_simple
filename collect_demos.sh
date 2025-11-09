#!/bin/bash

# UR5示教数据自动采集脚本
# 使用方法: ./collect_demos.sh <任务名称> <数量>

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 参数
TASK_NAME=${1:-"task1"}
NUM_DEMOS=${2:-15}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  UR5 Demonstration Collection${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Task: ${TASK_NAME}${NC}"
echo -e "${GREEN}Target: ${NUM_DEMOS} demonstrations${NC}"
echo ""

# 检查必要的节点
echo -e "${YELLOW}Checking ROS nodes...${NC}"

if ! rostopic list | grep -q "/joint_states"; then
    echo -e "${RED}✗ /joint_states not found. Is Gazebo running?${NC}"
    exit 1
fi

if ! rostopic list | grep -q "/eff_joint_traj_controller/command"; then
    echo -e "${RED}✗ Controller not found. Is Gazebo running?${NC}"
    exit 1
fi

if ! rosnode list | grep -q "demonstration_recorder"; then
    echo -e "${RED}✗ data_recorder.py not running!${NC}"
    echo -e "${YELLOW}Start it with: rosrun ur5_imitation data_recorder.py${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All nodes ready${NC}"
echo ""

# 创建任务目录
DEMO_DIR="$HOME/ur5_imitation_ws/src/ur5_imitation/demonstrations/${TASK_NAME}"
mkdir -p "$DEMO_DIR"

echo -e "${BLUE}Demonstrations will be saved to:${NC}"
echo -e "${BLUE}$DEMO_DIR${NC}"
echo ""

# 使用说明
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Instructions:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "1. Define your task clearly"
echo "2. For each demo:"
echo "   a. Move robot to starting position (keyboard)"
echo "   b. Press Enter to START recording"
echo "   c. Perform the task (5-15 seconds)"
echo "   d. Press Enter to STOP recording"
echo "3. Try to keep consistent task execution"
echo "4. Vary starting positions slightly"
echo ""
read -p "Press Enter to start collection..."

# 采集循环
SUCCESS_COUNT=0

for i in $(seq 1 $NUM_DEMOS); do
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Demo $i / $NUM_DEMOS${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # 步骤1：准备起始位置
    echo -e "${YELLOW}Step 1: Position the robot${NC}"
    echo "Use keyboard to move robot to starting position"
    echo "Try to vary the position slightly from previous demos"
    read -p "Press Enter when ready to record..."
    
    # 步骤2：开始记录
    echo -e "${GREEN}Step 2: Starting recording...${NC}"
    if rosservice call /start_recording; then
        echo -e "${GREEN}✓ Recording started${NC}"
    else
        echo -e "${RED}✗ Failed to start recording${NC}"
        continue
    fi
    
    # 步骤3：执行任务
    echo ""
    echo -e "${YELLOW}Step 3: PERFORM THE TASK NOW!${NC}"
    echo "Goal: Complete the task smoothly and consistently"
    echo "Tip: Avoid sudden stops or collisions"
    read -p "Press Enter when task is complete..."
    
    # 步骤4：停止记录
    echo -e "${GREEN}Step 4: Stopping recording...${NC}"
    if rosservice call /stop_recording; then
        echo -e "${GREEN}✓ Demo $i saved!${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}✗ Failed to stop recording${NC}"
        continue
    fi
    
    # 短暂休息
    echo ""
    echo -e "${BLUE}Progress: $SUCCESS_COUNT/$NUM_DEMOS completed${NC}"
    
    if [ $i -lt $NUM_DEMOS ]; then
        echo "Taking a short break (2 seconds)..."
        sleep 2
    fi
done

# 完成总结
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Collection Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Successfully collected: $SUCCESS_COUNT/$NUM_DEMOS demonstrations${NC}"
echo ""

# 检查数据
echo -e "${BLUE}Checking demonstration files...${NC}"
DEMO_FILES=$(ls ~/ur5_imitation_ws/src/ur5_imitation/demonstrations/*.h5 2>/dev/null | wc -l)
echo -e "${GREEN}Total .h5 files: $DEMO_FILES${NC}"

if [ $DEMO_FILES -ge 10 ]; then
    echo ""
    echo -e "${GREEN}✓ You have enough data to start training!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Review your demonstrations"
    echo "2. Run: cd ~/ur5_imitation_ws/src/ur5_imitation/scripts"
    echo "3. Run: python3 train_policy.py"
else
    echo ""
    echo -e "${YELLOW}⚠ You need at least 10 demonstrations${NC}"
    echo -e "${YELLOW}Current: $DEMO_FILES${NC}"
    echo "Run this script again to collect more!"
fi

echo ""
echo -e "${BLUE}Happy training! 🚀${NC}"
