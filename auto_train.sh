#!/bin/bash

# UR5 自动训练脚本
# 自动训练模型并生成报告

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  UR5 Automatic Training Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查当前目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_ROOT="$HOME/ur5_imitation_ws/src/ur5_imitation"
DEMO_DIR="$WORKSPACE_ROOT/demonstrations"
SCRIPTS_DIR="$WORKSPACE_ROOT/scripts"
MODELS_DIR="$WORKSPACE_ROOT/models"

# 步骤1：检查demonstrations
echo -e "${BLUE}[1/5] Checking demonstrations...${NC}"

if [ ! -d "$DEMO_DIR" ]; then
    echo -e "${RED}✗ Demonstrations directory not found: $DEMO_DIR${NC}"
    exit 1
fi

DEMO_COUNT=$(ls $DEMO_DIR/*.h5 2>/dev/null | wc -l)
echo -e "${GREEN}Found $DEMO_COUNT demonstration files${NC}"

if [ $DEMO_COUNT -lt 10 ]; then
    echo -e "${RED}✗ Insufficient demonstrations (need at least 10)${NC}"
    echo -e "${YELLOW}Current: $DEMO_COUNT${NC}"
    echo -e "${YELLOW}Please collect more demonstrations first!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Demonstrations check passed${NC}"
echo ""

# 步骤2：数据质量检查
echo -e "${BLUE}[2/5] Checking data quality...${NC}"

if command -v python3 &> /dev/null; then
    # 检查是否有check_demo_quality.py
    if [ -f "$SCRIPT_DIR/check_demo_quality.py" ]; then
        echo "Running quality check..."
        python3 "$SCRIPT_DIR/check_demo_quality.py" "$DEMO_DIR"
        echo ""
    else
        echo -e "${YELLOW}⚠ Quality check script not found, skipping...${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Python3 not found, skipping quality check${NC}"
fi

echo ""

# 步骤3：检查依赖
echo -e "${BLUE}[3/5] Checking dependencies...${NC}"

python3 -c "import torch" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ PyTorch not installed${NC}"
    echo -e "${YELLOW}Installing PyTorch...${NC}"
    pip3 install torch --break-system-packages
fi

python3 -c "import h5py" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing h5py...${NC}"
    pip3 install h5py --break-system-packages
fi

python3 -c "import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing numpy...${NC}"
    pip3 install numpy --break-system-packages
fi

python3 -c "import matplotlib" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing matplotlib...${NC}"
    pip3 install matplotlib --break-system-packages
fi

echo -e "${GREEN}✓ Dependencies ready${NC}"
echo ""

# 步骤4：训练模型
echo -e "${BLUE}[4/5] Training model...${NC}"

if [ ! -f "$SCRIPTS_DIR/train_policy.py" ]; then
    echo -e "${RED}✗ Training script not found: $SCRIPTS_DIR/train_policy.py${NC}"
    exit 1
fi

cd "$SCRIPTS_DIR"
echo -e "${GREEN}Starting training in: $SCRIPTS_DIR${NC}"
echo -e "${YELLOW}This may take 5-15 minutes...${NC}"
echo ""

# 运行训练
python3 train_policy.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Training completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Training failed${NC}"
    exit 1
fi

echo ""

# 步骤5：检查模型
echo -e "${BLUE}[5/5] Checking trained model...${NC}"

if [ -f "$MODELS_DIR/bc_policy_best.pth" ]; then
    MODEL_SIZE=$(du -h "$MODELS_DIR/bc_policy_best.pth" | cut -f1)
    echo -e "${GREEN}✓ Model saved: bc_policy_best.pth (${MODEL_SIZE})${NC}"
else
    echo -e "${RED}✗ Model file not found${NC}"
    exit 1
fi

if [ -f "$MODELS_DIR/training_curves.png" ]; then
    echo -e "${GREEN}✓ Training curves saved${NC}"
fi

echo ""

# 完成总结
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Training Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Model location:${NC}"
echo "  $MODELS_DIR/bc_policy_best.pth"
echo ""
echo -e "${BLUE}Training curves:${NC}"
echo "  $MODELS_DIR/training_curves.png"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review training curves:"
echo "   eog $MODELS_DIR/training_curves.png"
echo ""
echo "2. Test the model:"
echo "   # Terminal 1"
echo "   roslaunch ur5_imitation ur5_gazebo.launch"
echo ""
echo "   # Terminal 2"
echo "   rosrun ur5_imitation execute_policy.py $MODELS_DIR/bc_policy_best.pth"
echo ""
echo -e "${GREEN}Happy robot learning! 🤖${NC}"
