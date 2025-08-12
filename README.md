# 实时同声传译系统

一个支持中文和西班牙语双向实时翻译的同声传译系统，使用OpenAI的GPT模型进行高质量翻译，并提供双屏字幕显示功能。

## 功能特性

- 🎤 **实时语音识别**：支持中文和西班牙语的实时语音识别
- 🔄 **双向翻译**：中文↔西班牙语双向翻译，一键切换
- 📺 **双屏字幕显示**：源语言和目标语言分屏显示，实时滚动
- 🤖 **GPT驱动翻译**：使用OpenAI最强大的语言模型进行翻译
- ⏸️ **灵活控制**：支持开始、暂停、停止等操作
- 💾 **历史记录**：可导出翻译历史记录
- ⌨️ **快捷键支持**：F1-F4快捷键快速控制

## 系统要求

- Python 3.8+
- 麦克风设备
- 网络连接（用于API调用）
- OpenAI API密钥

## 安装指南

### 1. 克隆项目

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. 安装系统依赖

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev python3-tk
```

#### macOS
```bash
brew install portaudio
```

#### Windows
PyAudio通常需要预编译的wheel文件，可以从[这里](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)下载。

### 3. 安装Python依赖

```bash
pip install -r requirements.txt
```

或者使用安装脚本：

```bash
python install.py
```

### 4. 配置API密钥

#### 方法1：环境变量
```bash
export OPENAI_API_KEY="your-api-key-here"
```

#### 方法2：配置文件
运行程序后会自动生成`config.ini`文件，编辑该文件：

```ini
[API]
openai_key = your-api-key-here
```

## 使用说明

### 启动程序

运行V2版本（推荐）：
```bash
python real_time_translator_v2.py
```

或运行V1版本：
```bash
python real_time_translator.py
```

### 操作界面

1. **开始翻译** (F1)：点击开始按钮或按F1键开始录音和翻译
2. **暂停/继续** (F2)：暂停或继续翻译服务
3. **停止翻译** (F3)：停止所有翻译服务
4. **切换语言** (F4)：切换源语言和目标语言方向

### 界面说明

- **左屏**：显示源语言的识别文本
- **右屏**：显示翻译后的目标语言文本
- **状态栏**：显示当前状态、音频级别、翻译计数和API连接状态

## 配置选项

编辑`config.ini`文件可以自定义以下选项：

```ini
[API]
openai_key = your-api-key-here
openai_base_url = https://api.openai.com/v1

[Audio]
sample_rate = 16000
energy_threshold = 2000
pause_threshold = 0.8
max_phrase_duration = 5

[Translation]
model = gpt-4-turbo-preview
temperature = 0.3
max_tokens = 500

[Display]
font_size_source = 14
font_size_target = 14
window_width = 1400
window_height = 800
```

## 故障排除

### 常见问题

1. **麦克风无法识别**
   - 检查系统麦克风权限
   - 调整`energy_threshold`参数
   - 确保麦克风设备正常工作

2. **API连接失败**
   - 检查API密钥是否正确
   - 确保网络连接正常
   - 检查API余额

3. **翻译质量问题**
   - 尝试调整`temperature`参数
   - 使用更强大的模型（如gpt-4）

## 导出数据

点击"导出记录"按钮可以将翻译历史导出为JSON格式：

```json
[
  {
    "timestamp": "14:30:25",
    "source": "你好，欢迎使用翻译系统",
    "target": "Hola, bienvenido al sistema de traducción",
    "source_lang": "zh-CN",
    "target_lang": "es"
  }
]
```

## 注意事项

- 请确保在安静的环境中使用，以提高语音识别准确率
- 说话时请保持适当的语速和清晰度
- API调用会产生费用，请注意使用量
- 首次运行时需要下载语音识别模型，可能需要一些时间

## 版本说明

- **V1版本**：基础功能实现，使用旧版OpenAI API
- **V2版本**：改进的音频处理，更好的UI，使用最新OpenAI API

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！