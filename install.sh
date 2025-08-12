#!/bin/bash

# 实时同传翻译程序安装脚本

echo "=========================================="
echo "实时同传翻译程序 - 安装脚本"
echo "=========================================="

# 检查Python版本
echo "检查Python版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python3，请先安装Python3.8或更高版本"
    exit 1
fi

# 检查pip
echo "检查pip..."
python3 -m pip --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到pip，请先安装pip"
    exit 1
fi

# 升级pip
echo "升级pip..."
python3 -m pip install --upgrade pip

# 安装系统依赖
echo "安装系统依赖..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y python3-dev portaudio19-dev python3-pyaudio
    sudo apt-get install -y libasound2-dev
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y python3-devel portaudio-devel
    sudo yum install -y alsa-lib-devel
elif command -v pacman &> /dev/null; then
    # Arch Linux
    sudo pacman -S --noconfirm python-pip portaudio
else
    echo "警告: 未知的Linux发行版，请手动安装portaudio开发包"
fi

# 安装Python依赖
echo "安装Python依赖..."
python3 -m pip install -r requirements.txt

# 检查安装结果
echo "检查安装结果..."
python3 -c "
try:
    import speech_recognition
    import pygame
    import openai
    import sounddevice
    print('✓ 所有Python依赖安装成功')
except ImportError as e:
    print(f'✗ 依赖安装失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "错误: Python依赖安装失败"
    exit 1
fi

# 创建配置文件
echo "创建配置文件..."
if [ ! -f .env ]; then
    echo "创建.env配置文件..."
    cp .env.example .env
    echo "请在.env文件中设置您的OpenAI API密钥"
else
    echo ".env文件已存在"
fi

# 设置权限
echo "设置执行权限..."
chmod +x real_time_translator.py
chmod +x test_components.py

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 编辑.env文件，设置您的OpenAI API密钥"
echo "2. 运行测试: python3 test_components.py"
echo "3. 运行程序: python3 real_time_translator.py"
echo ""
echo "注意事项："
echo "- 确保麦克风正常工作"
echo "- 确保网络连接正常（用于OpenAI API调用）"
echo "- 程序需要全屏显示权限"
echo ""
echo "如有问题，请查看README.md文件或运行测试脚本"