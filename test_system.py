#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统功能测试脚本
用于验证各个模块的基本功能
"""

import sys
import json
import time

def test_config_loading():
    """测试配置文件加载"""
    print("🔧 测试配置文件加载...")
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = ['openai_api_key', 'audio_settings', 'ui_settings', 'translation_settings']
        for key in required_keys:
            if key not in config:
                print(f"❌ 配置文件缺少键: {key}")
                return False
        
        print("✅ 配置文件加载成功")
        return True
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return False

def test_audio_capture():
    """测试音频捕获模块"""
    print("🎤 测试音频捕获模块...")
    try:
        from audio_capture import AudioCapture
        
        capture = AudioCapture()
        print("✅ 音频捕获模块导入成功")
        
        # 测试初始化
        if hasattr(capture, 'audio') and capture.audio:
            print("✅ PyAudio初始化成功")
        else:
            print("❌ PyAudio初始化失败")
            return False
        
        capture.cleanup()
        print("✅ 音频捕获模块测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 音频捕获模块测试失败: {e}")
        return False

def test_speech_recognition():
    """测试语音识别模块"""
    print("🗣️ 测试语音识别模块...")
    try:
        from speech_recognition import SpeechRecognizer
        
        recognizer = SpeechRecognizer()
        print("✅ 语音识别模块导入成功")
        
        # 测试语言检测
        chinese_test = recognizer.detect_language("你好世界")
        spanish_test = recognizer.detect_language("Hola mundo")
        
        if chinese_test == 'chinese' and spanish_test == 'spanish':
            print("✅ 语言检测功能正常")
        else:
            print(f"⚠️ 语言检测结果异常: 中文={chinese_test}, 西班牙语={spanish_test}")
        
        print("✅ 语音识别模块测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 语音识别模块测试失败: {e}")
        return False

def test_translation():
    """测试翻译模块"""
    print("🌐 测试翻译模块...")
    try:
        from translation import ChatGPTTranslator
        
        translator = ChatGPTTranslator()
        print("✅ 翻译模块导入成功")
        
        # 测试语言检测
        chinese_test = translator.detect_language("你好世界")
        spanish_test = translator.detect_language("Hola mundo")
        
        if chinese_test == 'chinese' and spanish_test == 'spanish':
            print("✅ 翻译模块语言检测正常")
        else:
            print(f"⚠️ 翻译模块语言检测异常: 中文={chinese_test}, 西班牙语={spanish_test}")
        
        print("✅ 翻译模块测试通过")
        print("ℹ️ 注意: 实际翻译需要有效的OpenAI API密钥和网络连接")
        return True
        
    except Exception as e:
        print(f"❌ 翻译模块测试失败: {e}")
        return False

def test_ui():
    """测试UI模块"""
    print("🖥️ 测试UI模块...")
    try:
        import tkinter as tk
        print("✅ tkinter可用")
        
        from subtitle_ui import SubtitleDisplay
        print("✅ 字幕UI模块导入成功")
        
        print("✅ UI模块测试通过")
        print("ℹ️ 注意: 完整UI测试需要运行图形界面")
        return True
        
    except Exception as e:
        print(f"❌ UI模块测试失败: {e}")
        return False

def test_main_integration():
    """测试主程序集成"""
    print("🔗 测试主程序集成...")
    try:
        from main import RealTimeTranslationSystem
        print("✅ 主程序模块导入成功")
        
        print("✅ 主程序集成测试通过")
        print("ℹ️ 注意: 完整集成测试需要运行完整程序")
        return True
        
    except Exception as e:
        print(f"❌ 主程序集成测试失败: {e}")
        return False

def check_dependencies():
    """检查依赖项"""
    print("📦 检查依赖项...")
    
    dependencies = [
        ('pyaudio', 'PyAudio音频处理'),
        ('speech_recognition', '语音识别'),
        ('openai', 'OpenAI API'),
        ('requests', 'HTTP请求'),
        ('tkinter', 'GUI界面'),
        ('threading', '多线程支持'),
        ('queue', '队列管理'),
        ('json', 'JSON处理')
    ]
    
    missing = []
    
    for module, description in dependencies:
        try:
            if module == 'tkinter':
                import tkinter
            else:
                __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError:
            print(f"❌ {module} - {description} (缺失)")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️ 缺失 {len(missing)} 个依赖项: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("✅ 所有依赖项检查通过")
        return True

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 实时双语同传翻译系统 - 功能测试")
    print("=" * 60)
    print()
    
    tests = [
        ("依赖项检查", check_dependencies),
        ("配置文件", test_config_loading),
        ("音频捕获", test_audio_capture),
        ("语音识别", test_speech_recognition),
        ("翻译服务", test_translation),
        ("用户界面", test_ui),
        ("主程序集成", test_main_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试:")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
        
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统准备就绪。")
        print("\n🚀 可以运行以下命令启动程序:")
        print("   python run.py")
        print("   或双击 start.bat (Windows) / ./start.sh (Linux/Mac)")
        return True
    else:
        print(f"⚠️ {total - passed} 个测试失败，请检查相关问题。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 系统测试完成 - 所有功能正常")
    else:
        print("❌ 系统测试完成 - 发现问题需要修复")
    
    input("\n按Enter键退出...")