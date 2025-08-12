# 中西实时同传 (CN ⇄ ES-MX)

基于浏览器麦克风与 OpenAI，实时将中文与墨西哥西班牙语相互翻译，并以双栏滚动字幕显示。

## 功能
- 浏览器直接采集麦克风音频
- 服务端调用 OpenAI 语音识别（优先 gpt-4o-mini-transcribe，降级 whisper-1）
- 使用 GPT-4o 做高质量中西互译
- Web 界面双列同步显示中文与西语字幕，自动滚动

## 环境准备
1. 安装 Python 3.10+
2. 准备 OpenAI API Key 并导出：
   - Linux/macOS:
     ```bash
     export OPENAI_API_KEY=sk-...your_key...
     ```
   - 或在项目根目录创建 `.env`，内容：
     ```
     OPENAI_API_KEY=sk-...your_key...
     ```

## 安装依赖
```bash
pip install -r requirements.txt
```

## 运行
```bash
python server.py
```
浏览器打开 `http://localhost:5000`，点击“开始”授予麦克风权限即可。

## 备注
- 如需指定翻译模型，设置环境变量：
  ```bash
  export TRANSLATION_MODEL=gpt-4o
  ```
- 如果网络环境不稳定，可适当增大前端 `MediaRecorder.start(1000)` 的分片时长。
- 本项目为演示用，未做高级分段与拼接，实际部署建议加入语音活动检测（VAD）与缓冲队列，平衡延迟与准确率。