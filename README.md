# 实时双语同传翻译系统

一个支持中文与西班牙语实时音频翻译和字幕显示的Python应用程序，使用ChatGPT API提供高质量的翻译服务。

## 功能特性

- 🎤 **实时音频捕获**: 支持麦克风音频实时录制
- 🗣️ **语音识别**: 自动识别中文和西班牙语语音
- 🌐 **智能翻译**: 使用ChatGPT API进行高质量翻译
- 📺 **双屏字幕**: 同时显示原文和译文的滚动字幕
- 💾 **记录保存**: 支持保存翻译历史记录
- ⚙️ **可配置**: 丰富的配置选项和界面设置

## 系统要求

- Python 3.7+
- 有效的麦克风设备
- 网络连接 (用于语音识别和翻译API)
- OpenAI API密钥

## 安装步骤

### 1. 克隆或下载项目

```bash
# 如果使用git
git clone <repository-url>
cd real-time-translation

# 或者直接下载项目文件到本地文件夹
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

**注意**: 如果安装pyaudio时遇到问题，请根据您的操作系统执行以下操作：

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-pyaudio
```

### 3. 配置API密钥

编辑 `config.json` 文件，将您的OpenAI API密钥填入：

```json
{
    "openai_api_key": "您的_OPENAI_API_密钥_在这里",
    ...
}
```

## 使用方法

### 启动程序

```bash
python main.py
```

### 操作步骤

1. **启动程序**: 运行 `python main.py`
2. **检查配置**: 确保API密钥已正确配置
3. **开始录音**: 点击界面上的"开始录音"按钮
4. **开始说话**: 对着麦克风说中文或西班牙语
5. **查看翻译**: 翻译结果会实时显示在双屏字幕区域
6. **保存记录**: 可以点击"保存记录"保存翻译历史
7. **停止录音**: 点击"停止录音"结束翻译

### 界面功能

- **开始/停止录音**: 控制音频录制和翻译
- **清除字幕**: 清空所有显示的字幕内容
- **保存记录**: 将翻译历史保存为文本或JSON文件
- **自动滚动**: 自动滚动到最新的字幕内容
- **显示时间戳**: 在字幕前显示时间戳
- **字体大小调节**: 实时调整字幕字体大小

## 配置文件说明

`config.json` 文件包含以下配置项：

### OpenAI API设置
```json
{
    "openai_api_key": "您的API密钥",
    "translation_settings": {
        "model": "gpt-4-turbo-preview",  // 使用的GPT模型
        "max_tokens": 1000,              // 最大令牌数
        "temperature": 0.3               // 翻译创造性(0-1)
    }
}
```

### 音频设置
```json
{
    "audio_settings": {
        "sample_rate": 16000,      // 采样率
        "chunk_size": 1024,        // 音频块大小
        "channels": 1,             // 声道数(单声道)
        "silence_threshold": 1000, // 静音阈值
        "min_audio_length": 1.0    // 最小音频长度(秒)
    }
}
```

### 界面设置
```json
{
    "ui_settings": {
        "window_width": 800,           // 窗口宽度
        "window_height": 600,          // 窗口高度
        "font_size": 14,               // 默认字体大小
        "font_family": "Microsoft YaHei", // 字体族
        "bg_color": "#1e1e1e",         // 背景颜色
        "chinese_color": "#00ff88",    // 中文文字颜色
        "spanish_color": "#ffaa00"     // 西班牙语文字颜色
    }
}
```

## 支持的语言

- **中文 (Chinese)**: 简体中文语音识别和文本
- **西班牙语 (Spanish)**: 西班牙语语音识别和文本
- **自动检测**: 系统会自动检测输入语言并翻译为对应的目标语言

## 故障排除

### 常见问题

**1. 无法录音/没有声音输入**
- 检查麦克风是否正常工作
- 确认系统麦克风权限已授予Python应用
- 检查音频设备是否被其他程序占用

**2. 语音识别失败**
- 确保网络连接正常
- 检查Google语音识别服务是否可用
- 尝试说话更清晰，避免背景噪音

**3. 翻译API错误**
- 验证OpenAI API密钥是否正确
- 检查API配额和余额
- 确认网络可以访问OpenAI服务

**4. 界面显示问题**
- 确保系统支持tkinter
- 检查字体设置是否正确
- 尝试调整窗口大小

### 错误代码

- `API认证失败`: OpenAI API密钥无效
- `API调用频率限制`: 超出API调用限制
- `录音错误`: 音频设备问题
- `识别请求错误`: 语音识别服务问题

## 性能优化

### 提高翻译速度
- 使用更快的GPT模型 (如gpt-3.5-turbo)
- 降低max_tokens值
- 启用翻译缓存功能

### 降低延迟
- 调整音频块大小
- 优化静音检测阈值
- 减少音频处理缓冲区

### 节省API费用
- 使用翻译缓存避免重复翻译
- 选择合适的模型平衡质量和成本
- 设置合理的max_tokens限制

## 项目结构

```
real-time-translation/
├── main.py                 # 主程序入口
├── audio_capture.py        # 音频捕获模块
├── speech_recognition.py   # 语音识别模块
├── translation.py          # 翻译服务模块
├── subtitle_ui.py          # 字幕显示界面
├── config.json            # 配置文件
├── requirements.txt       # Python依赖
└── README.md             # 说明文档
```

## 技术架构

系统采用模块化设计，包含以下主要组件：

1. **音频捕获**: 使用pyaudio实时录制麦克风音频
2. **语音识别**: 使用Google Speech Recognition API
3. **翻译服务**: 使用OpenAI ChatGPT API
4. **用户界面**: 使用tkinter构建GUI界面
5. **多线程处理**: 确保实时性能和响应能力

## 开发信息

- **开发语言**: Python 3.7+
- **主要依赖**: pyaudio, speech_recognition, openai, tkinter
- **架构模式**: 模块化设计，异步处理
- **版本**: 1.0.0

## 许可证

本项目仅供学习和研究使用。使用时请遵守相关API服务的使用条款。

## 联系支持

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件反馈
- 查看项目文档

---

**注意**: 使用本系统需要有效的OpenAI API密钥，并且会产生API调用费用。请合理使用并注意成本控制。