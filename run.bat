@echo off
chcp 65001 >nul
title 实时同声传译系统

echo ==========================================
echo 实时同声传译系统
echo ==========================================

:: 检查Python版本
python --version

:: 检查是否存在虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

:: 检查配置文件
if not exist "config.ini" (
    echo 配置文件不存在，创建默认配置...
    python -c "import configparser; config = configparser.ConfigParser(); config['API'] = {'openai_key': 'your-openai-api-key-here', 'openai_base_url': 'https://api.openai.com/v1'}; config['Audio'] = {'sample_rate': '16000', 'chunk_size': '1024', 'energy_threshold': '2000', 'pause_threshold': '0.8', 'phrase_threshold': '0.3', 'max_phrase_duration': '5'}; config['Translation'] = {'model': 'gpt-4-turbo-preview', 'temperature': '0.3', 'max_tokens': '500'}; config['Display'] = {'font_size_source': '14', 'font_size_target': '14', 'window_width': '1400', 'window_height': '800'}; config.write(open('config.ini', 'w'))"
    echo 配置文件已创建: config.ini
    echo 请编辑配置文件并添加您的OpenAI API密钥
)

:: 检查OpenAI API密钥
if "%OPENAI_API_KEY%"=="" (
    echo.
    echo 警告: 未设置OPENAI_API_KEY环境变量
    echo 您可以：
    echo 1. set OPENAI_API_KEY=your-api-key-here
    echo 2. 或在config.ini中设置API密钥
    echo.
)

:: 选择版本
echo.
echo 请选择要运行的版本：
echo 1. V2版本 (推荐 - 改进的音频处理和UI)
echo 2. V1版本 (基础版本)
echo.
set /p version_choice=请输入选择 (1 或 2): 

if "%version_choice%"=="1" (
    echo 启动V2版本...
    python real_time_translator_v2.py
) else if "%version_choice%"=="2" (
    echo 启动V1版本...
    python real_time_translator.py
) else (
    echo 无效选择，启动默认V2版本...
    python real_time_translator_v2.py
)

pause