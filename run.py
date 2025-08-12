#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时双语同传翻译系统 - 启动脚本
简化的启动入口，包含自动配置检查和友好的用户提示
"""

import os
import sys
import json
import subprocess
from tkinter import messagebox, simpledialog
import tkinter as tk

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    return True

def check_config_file():
    """检查并配置config.json文件"""
    config_file = "config.json"
    
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查API密钥
        if config.get('openai_api_key') == "YOUR_OPENAI_API_KEY_HERE":
            print("需要配置OpenAI API密钥...")
            
            # 创建简单的输入对话框
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            
            api_key = simpledialog.askstring(
                "API密钥配置",
                "请输入您的OpenAI API密钥:\n\n"
                "如果您还没有API密钥，请访问:\n"
                "https://platform.openai.com/api-keys\n\n"
                "API密钥:",
                show='*'
            )
            
            if not api_key:
                messagebox.showerror("错误", "需要API密钥才能运行程序")
                return False
            
            # 更新配置文件
            config['openai_api_key'] = api_key
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("成功", "API密钥已保存，程序即将启动")
            root.destroy()
        
        return True
        
    except Exception as e:
        print(f"配置文件读取错误: {e}")
        return False

def check_dependencies():
    """检查并安装依赖项"""
    print("检查依赖项...")
    
    required_modules = {
        'pyaudio': 'PyAudio',
        'speech_recognition': 'SpeechRecognition', 
        'openai': 'openai',
        'requests': 'requests'
    }
    
    missing_modules = []
    
    for module, pip_name in required_modules.items():
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (缺失)")
            missing_modules.append(pip_name)
    
    # 检查tkinter
    try:
        import tkinter
        print("✓ tkinter")
    except ImportError:
        print("✗ tkinter (缺失)")
        print("错误: tkinter是Python标准库的一部分，请检查Python安装")
        return False
    
    if missing_modules:
        print(f"\n缺失 {len(missing_modules)} 个依赖项")
        
        # 询问是否自动安装
        root = tk.Tk()
        root.withdraw()
        
        install = messagebox.askyesno(
            "安装依赖",
            f"检测到缺失的依赖项:\n{', '.join(missing_modules)}\n\n"
            "是否自动安装这些依赖项？\n"
            "（需要网络连接）"
        )
        
        root.destroy()
        
        if install:
            print("正在安装依赖项...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
                ])
                print("✓ 依赖项安装完成")
                return True
            except subprocess.CalledProcessError as e:
                print(f"依赖项安装失败: {e}")
                return False
        else:
            print("请手动安装依赖项: pip install -r requirements.txt")
            return False
    
    print("✓ 所有依赖项检查通过")
    return True

def check_audio_device():
    """检查音频设备"""
    try:
        import pyaudio
        
        audio = pyaudio.PyAudio()
        
        # 检查输入设备
        input_devices = []
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])
        
        audio.terminate()
        
        if not input_devices:
            print("警告: 未检测到可用的音频输入设备")
            return False
        
        print(f"✓ 检测到 {len(input_devices)} 个音频输入设备")
        return True
        
    except Exception as e:
        print(f"音频设备检查失败: {e}")
        return False

def show_startup_info():
    """显示启动信息"""
    print("\n" + "="*60)
    print("🎤 实时双语同传翻译系统")
    print("支持中文 ↔ 西班牙语实时翻译")
    print("="*60)
    print("\n📋 启动检查:")

def show_usage_tips():
    """显示使用提示"""
    root = tk.Tk()
    root.withdraw()
    
    tips = """
🎯 使用提示:

1. 📢 确保麦克风工作正常，环境相对安静
2. 🗣️ 清晰地说话，避免过快或过慢
3. ⏸️ 句子之间留有适当的停顿
4. 🌐 保持网络连接稳定
5. 💡 首次使用可能需要几秒钟初始化

🔧 界面功能:
• 开始/停止录音：控制翻译开关
• 清除字幕：清空显示内容  
• 保存记录：保存翻译历史
• 字体调节：调整显示大小

❓ 如有问题请查看README.md文档
    """
    
    messagebox.showinfo("使用提示", tips)
    root.destroy()

def main():
    """主启动函数"""
    show_startup_info()
    
    # 检查Python版本
    if not check_python_version():
        input("按Enter键退出...")
        sys.exit(1)
    
    # 检查依赖项
    if not check_dependencies():
        input("按Enter键退出...")
        sys.exit(1)
    
    # 检查配置文件
    if not check_config_file():
        input("按Enter键退出...")
        sys.exit(1)
    
    # 检查音频设备
    if not check_audio_device():
        print("警告: 音频设备检查失败，可能影响录音功能")
    
    print("\n✅ 所有检查完成，准备启动程序...")
    
    # 显示使用提示
    show_usage_tips()
    
    try:
        # 启动主程序
        print("🚀 启动主程序...")
        from main import main as main_program
        main_program()
        
    except KeyboardInterrupt:
        print("\n👋 程序被用户终止")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")
    
    print("程序已退出")

if __name__ == "__main__":
    main()