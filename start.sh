#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n=============================================="
echo -e "  ${BLUE}实时双语同传翻译系统${NC}"
echo -e "  ${YELLOW}支持中文 ↔ 西班牙语实时翻译${NC}"
echo -e "==============================================\n"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到Python${NC}"
        echo "请先安装Python 3.7或更高版本"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 检查Python版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+')
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ 错误: Python版本过低${NC}"
    echo "当前版本: $PYTHON_VERSION"
    echo "需要版本: $REQUIRED_VERSION 或更高"
    exit 1
fi

# 检查当前目录是否正确
if [ ! -f "run.py" ]; then
    echo -e "${RED}❌ 错误: 未找到run.py文件${NC}"
    echo "请确保在正确的项目目录中运行此脚本"
    exit 1
fi

# 启动程序
echo -e "${GREEN}🚀 正在启动翻译系统...${NC}"
$PYTHON_CMD run.py

# 程序结束
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo -e "\n${GREEN}✅ 程序正常退出${NC}"
else
    echo -e "\n${RED}❌ 程序异常退出 (代码: $exit_code)${NC}"
fi