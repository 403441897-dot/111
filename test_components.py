#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组件测试脚本 - 测试实时同传翻译程序的各个功能模块
"""

import os
import sys
import time
import threading
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_config():
    """测试配置模块"""
    print("=== 测试配置模块 ===")
    try:
        from config import Config
        config = Config()
        
        if config.validate():
            print("✓ 配置验证通过")
            config.print_config()
        else:
            print("✗ 配置验证失败")
            return False
            
        return True
    except Exception as e:
        print(f"✗ 配置模块测试失败: {e}")
        return False

def test_openai_connection():
    """测试OpenAI连接"""
    print("\n=== 测试OpenAI连接 ===")
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("✗ 未设置OPENAI_API_KEY")
            return False
            
        client = OpenAI(api_key=api_key)
        
        # 测试简单请求
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            print("✓ OpenAI连接测试成功")
            return True
        else:
            print("✗ OpenAI响应为空")
            return False
            
    except Exception as e:
        print(f"✗ OpenAI连接测试失败: {e}")
        return False

def test_audio_devices():
    """测试音频设备"""
    print("\n=== 测试音频设备 ===")
    try:
        import speech_recognition as sr
        
        # 获取可用麦克风
        mic_list = sr.Microphone.list_microphone_names()
        if mic_list:
            print(f"✓ 发现 {len(mic_list)} 个音频设备:")
            for i, name in enumerate(mic_list):
                print(f"  {i}: {name}")
        else:
            print("✗ 未发现音频设备")
            return False
            
        # 测试默认麦克风
        try:
            mic = sr.Microphone()
            with mic as source:
                print("✓ 默认麦克风可用")
        except Exception as e:
            print(f"✗ 默认麦克风测试失败: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 音频设备测试失败: {e}")
        return False

def test_display():
    """测试显示模块"""
    print("\n=== 测试显示模块 ===")
    try:
        import pygame
        
        pygame.init()
        
        # 测试窗口创建
        screen = pygame.display.set_mode((800, 600))
        print("✓ 窗口创建成功")
        
        # 测试字体
        font = pygame.font.SysFont("arial", 24)
        text_surface = font.render("测试文本", True, (255, 255, 255))
        print("✓ 字体渲染成功")
        
        # 测试绘制
        screen.fill((0, 0, 0))
        screen.blit(text_surface, (100, 100))
        pygame.display.flip()
        print("✓ 绘制功能正常")
        
        # 等待一秒显示
        time.sleep(1)
        
        pygame.quit()
        print("✓ 显示模块测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 显示模块测试失败: {e}")
        return False

def test_translation():
    """测试翻译功能"""
    print("\n=== 测试翻译功能 ===")
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("✗ 未设置OPENAI_API_KEY")
            return False
            
        client = OpenAI(api_key=api_key)
        
        # 测试中文到西班牙语翻译
        prompt = """请将以下中文文本翻译成墨西哥西班牙语。要求：
1. 保持原意准确
2. 使用自然流畅的表达
3. 使用墨西哥地区的常用表达方式
4. 只返回翻译结果，不要其他解释

原文：你好，很高兴认识你。

翻译："""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个专业的翻译专家，精通中文和墨西哥西班牙语。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        translation = response.choices[0].message.content.strip()
        print(f"✓ 翻译测试成功")
        print(f"  原文: 你好，很高兴认识你。")
        print(f"  翻译: {translation}")
        
        return True
        
    except Exception as e:
        print(f"✗ 翻译功能测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("开始运行组件测试...\n")
    
    tests = [
        ("配置模块", test_config),
        ("OpenAI连接", test_openai_connection),
        ("音频设备", test_audio_devices),
        ("显示模块", test_display),
        ("翻译功能", test_translation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n=== 测试结果汇总 ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！程序可以正常运行。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关配置。")
        return False

def main():
    """主函数"""
    print("实时同传翻译程序 - 组件测试")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("警告: 未设置OPENAI_API_KEY环境变量")
        print("请创建.env文件并设置您的OpenAI API密钥")
        print("示例: OPENAI_API_KEY=your_api_key_here")
        print()
    
    # 运行测试
    success = run_all_tests()
    
    if success:
        print("\n✅ 所有组件测试通过，可以运行主程序！")
        print("运行命令: python real_time_translator.py")
    else:
        print("\n❌ 部分组件测试失败，请解决问题后再运行主程序。")
    
    return success

if __name__ == "__main__":
    main()