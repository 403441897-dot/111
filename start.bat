@echo off
chcp 65001 >nul
title 实时双语同传翻译系统

echo.
echo ===============================================
echo   实时双语同传翻译系统
echo   支持中文 ↔ 西班牙语实时翻译
echo ===============================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 启动程序
echo 🚀 正在启动翻译系统...
python run.py

REM 程序结束后暂停
if errorlevel 1 (
    echo.
    echo ❌ 程序异常退出
) else (
    echo.
    echo ✅ 程序正常退出
)
pause