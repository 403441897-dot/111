#!/bin/bash

# 实时同传翻译程序启动脚本

echo "=========================================="
echo "实时同传翻译程序 - 启动脚本"
echo "=========================================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查配置文件
if [ ! -f .env ]; then
    echo "错误: 未找到.env配置文件"
    echo "请先运行安装脚本: ./install.sh"
    exit 1
fi

# 检查OpenAI API密钥
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "错误: 请在.env文件中设置有效的OpenAI API密钥"
    echo "编辑.env文件并设置: OPENAI_API_KEY=your_actual_api_key"
    exit 1
fi

# 检查依赖
echo "检查Python依赖..."
python3 -c "
try:
    import speech_recognition, pygame, openai, sounddevice
    print('✓ 依赖检查通过')
except ImportError as e:
    print(f'✗ 缺少依赖: {e}')
    print('请运行: ./install.sh')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 检查音频设备
echo "检查音频设备..."
python3 -c "
import speech_recognition as sr
try:
    mic_list = sr.Microphone.list_microphone_names()
    if mic_list:
        print(f'✓ 发现 {len(mic_list)} 个音频设备')
    else:
        print('✗ 未发现音频设备')
        exit(1)
except Exception as e:
    print(f'✗ 音频设备检查失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "音频设备检查失败，请检查麦克风连接"
    exit 1
fi

echo ""
echo "所有检查通过，启动程序..."
echo "提示: 按ESC键退出程序"
echo ""

# 启动程序
python3 real_time_translator.py