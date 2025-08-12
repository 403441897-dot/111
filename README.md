# 实时同传翻译程序

一个功能强大的实时墨西哥西班牙语与中文同传翻译程序，支持语音识别、ChatGPT翻译和双屏字幕显示。

## 🌟 主要功能

- **实时语音识别**: 支持中文和墨西哥西班牙语的实时语音输入
- **智能翻译**: 使用ChatGPT API进行高质量翻译
- **双屏字幕**: 实时显示原文和翻译，支持滚动历史记录
- **全屏显示**: 专为演示和会议场景设计
- **多线程处理**: 音频处理、翻译和显示分离，确保流畅运行

## 🚀 技术特点

- **多语言支持**: 自动检测输入语言（中文/西班牙语）
- **高质量翻译**: 使用GPT-4模型，确保翻译准确性
- **墨西哥特色**: 针对墨西哥西班牙语进行优化
- **实时性能**: 低延迟的语音识别和翻译
- **可配置**: 支持自定义显示设置和API参数

## 📋 系统要求

- **操作系统**: Linux (推荐Ubuntu 20.04+)
- **Python**: 3.8 或更高版本
- **内存**: 至少4GB RAM
- **网络**: 稳定的互联网连接（用于OpenAI API）
- **音频**: 工作正常的麦克风
- **显示**: 支持全屏显示的图形界面

## 🛠️ 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd real-time-translator
```

### 2. 运行安装脚本
```bash
chmod +x install.sh
./install.sh
```

### 3. 配置环境变量
编辑 `.env` 文件，设置您的OpenAI API密钥：
```bash
cp .env.example .env
nano .env
```

在 `.env` 文件中添加：
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 测试安装
```bash
python3 test_components.py
```

## 🔧 手动安装

如果自动安装失败，可以手动安装依赖：

### 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev portaudio19-dev python3-pyaudio libasound2-dev

# CentOS/RHEL
sudo yum install python3-devel portaudio-devel alsa-lib-devel

# Arch Linux
sudo pacman -S python-pip portaudio
```

### 安装Python依赖
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 🎯 使用方法

### 启动程序
```bash
python3 real_time_translator.py
```

### 操作说明
- **说话**: 对着麦克风说话，程序会自动识别语言
- **查看翻译**: 翻译结果会实时显示在屏幕上
- **退出程序**: 按 `ESC` 键退出
- **暂停/恢复**: 按空格键暂停或恢复（功能开发中）

### 显示界面
- **顶部**: 程序标题
- **中间**: 实时字幕显示区域
- **底部**: 操作提示信息

## ⚙️ 配置选项

可以通过修改 `.env` 文件来自定义程序行为：

```env
# OpenAI配置
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 显示配置
WINDOW_WIDTH=1920
WINDOW_HEIGHT=1080
FONT_SIZE=48
MAX_SUBTITLES=10

# 音频配置
ENERGY_THRESHOLD=4000
PAUSE_THRESHOLD=0.8
PHRASE_TIME_LIMIT=10

# 翻译配置
TRANSLATION_TIMEOUT=30
MAX_TOKENS=500
TEMPERATURE=0.3
```

## 🔍 故障排除

### 常见问题

1. **麦克风不工作**
   - 检查麦克风权限
   - 运行 `python3 test_components.py` 测试音频设备

2. **翻译失败**
   - 检查网络连接
   - 验证OpenAI API密钥
   - 检查API配额

3. **显示问题**
   - 确保支持全屏显示
   - 检查字体文件

4. **依赖安装失败**
   - 更新pip: `python3 -m pip install --upgrade pip`
   - 安装系统开发包
   - 使用虚拟环境

### 调试模式
程序会输出详细的日志信息，包括：
- 音频识别状态
- 翻译请求和响应
- 显示更新信息
- 错误详情

## 📁 项目结构

```
real-time-translator/
├── real_time_translator.py  # 主程序
├── config.py                # 配置管理
├── test_components.py       # 组件测试
├── requirements.txt         # Python依赖
├── install.sh              # 安装脚本
├── .env.example            # 环境变量示例
├── .env                    # 环境变量配置（需要创建）
└── README.md               # 说明文档
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证。

## 🙏 致谢

- OpenAI提供的强大翻译能力
- Google Speech Recognition的语音识别服务
- Pygame提供的图形界面支持
- 开源社区的贡献

## 📞 支持

如果您遇到问题或需要帮助，请：
1. 查看本文档的故障排除部分
2. 运行测试脚本检查组件状态
3. 提交Issue描述问题详情

---

**注意**: 使用本程序需要有效的OpenAI API密钥，请确保您有足够的API配额。