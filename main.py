#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时双语同传翻译系统
支持中文与西班牙语的实时音频翻译和字幕显示

作者: AI Assistant
版本: 1.0.0
"""

import sys
import os
import threading
import time
import json
import traceback
from tkinter import messagebox

# 导入自定义模块
from audio_capture import AudioCapture
from speech_recognition import SpeechRecognitionService
from translation import TranslationService
from subtitle_ui import SubtitleDisplay

class RealTimeTranslationSystem:
    """实时翻译系统主类"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.load_config()
        
        # 初始化各个组件
        self.audio_capture = None
        self.speech_recognition = None
        self.translation_service = None
        self.subtitle_display = None
        
        # 系统状态
        self.is_running = False
        self.processing_thread = None
        
        # 初始化组件
        self.init_components()
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print("配置文件加载成功")
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            sys.exit(1)
    
    def init_components(self):
        """初始化系统组件"""
        try:
            print("正在初始化系统组件...")
            
            # 检查OpenAI API密钥
            if self.config['openai_api_key'] == "YOUR_OPENAI_API_KEY_HERE":
                messagebox.showerror(
                    "配置错误", 
                    "请在config.json文件中设置您的OpenAI API密钥\n"
                    "将 'YOUR_OPENAI_API_KEY_HERE' 替换为您的实际API密钥"
                )
                sys.exit(1)
            
            # 初始化音频捕获
            self.audio_capture = AudioCapture(self.config_file)
            print("✓ 音频捕获模块初始化完成")
            
            # 初始化语音识别
            self.speech_recognition = SpeechRecognitionService(self.config_file)
            print("✓ 语音识别模块初始化完成")
            
            # 初始化翻译服务
            self.translation_service = TranslationService(self.config_file)
            print("✓ 翻译服务模块初始化完成")
            
            # 初始化字幕显示界面
            self.subtitle_display = SubtitleDisplay(self.config_file)
            self.subtitle_display.set_callbacks(
                on_start=self.start_translation,
                on_stop=self.stop_translation
            )
            print("✓ 字幕显示界面初始化完成")
            
            print("系统初始化完成！")
            
        except Exception as e:
            print(f"系统初始化失败: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    def start_translation(self):
        """开始实时翻译"""
        if self.is_running:
            return
        
        try:
            print("启动实时翻译系统...")
            self.is_running = True
            
            # 启动各个服务
            self.audio_capture.start_recording()
            self.speech_recognition.start_service()
            self.translation_service.start_service()
            
            # 启动处理线程
            self.processing_thread = threading.Thread(target=self.process_audio_loop, daemon=True)
            self.processing_thread.start()
            
            self.subtitle_display.update_status("正在录音和翻译...")
            print("实时翻译系统已启动")
            
        except Exception as e:
            print(f"启动翻译系统失败: {e}")
            traceback.print_exc()
            self.stop_translation()
    
    def stop_translation(self):
        """停止实时翻译"""
        if not self.is_running:
            return
        
        try:
            print("停止实时翻译系统...")
            self.is_running = False
            
            # 停止各个服务
            if self.audio_capture:
                self.audio_capture.stop_recording()
            
            if self.speech_recognition:
                self.speech_recognition.stop_service()
            
            if self.translation_service:
                self.translation_service.stop_service()
            
            # 等待处理线程结束
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2)
            
            self.subtitle_display.update_status("已停止录音")
            print("实时翻译系统已停止")
            
        except Exception as e:
            print(f"停止翻译系统时出错: {e}")
            traceback.print_exc()
    
    def process_audio_loop(self):
        """音频处理主循环"""
        print("音频处理循环开始")
        
        while self.is_running:
            try:
                # 获取音频数据
                audio_data = self.audio_capture.get_audio_data()
                if audio_data:
                    print(f"获取到音频数据: {len(audio_data)} 字节")
                    
                    # 发送到语音识别
                    self.speech_recognition.add_audio_for_recognition(
                        audio_data, 
                        self.config['audio_settings']['sample_rate']
                    )
                
                # 获取语音识别结果
                recognition_result = self.speech_recognition.get_recognition_result()
                if recognition_result and 'best_result' in recognition_result:
                    text = recognition_result['best_result']
                    source_lang = recognition_result['detected_language']
                    
                    print(f"识别结果 ({source_lang}): {text}")
                    
                    # 发送到翻译服务
                    self.translation_service.add_text_for_translation(text, source_lang)
                
                # 获取翻译结果
                translation_result = self.translation_service.get_translation_result()
                if translation_result and translation_result.get('success'):
                    original_text = translation_result['original_text']
                    translated_text = translation_result['translated_text']
                    source_lang = translation_result['source_language']
                    target_lang = translation_result['target_language']
                    
                    print(f"翻译结果 ({source_lang} -> {target_lang}): {translated_text}")
                    
                    # 显示字幕
                    self.subtitle_display.add_subtitle(
                        original_text, 
                        translated_text, 
                        source_lang, 
                        target_lang
                    )
                    
                    # 更新状态
                    cache_status = "缓存" if translation_result.get('from_cache') else "实时"
                    self.subtitle_display.update_status(f"翻译完成 ({cache_status}) - {source_lang} -> {target_lang}")
                
                # 短暂休眠避免CPU占用过高
                time.sleep(0.05)
                
            except Exception as e:
                print(f"音频处理循环错误: {e}")
                traceback.print_exc()
                time.sleep(0.1)
        
        print("音频处理循环结束")
    
    def run(self):
        """运行主程序"""
        try:
            print("启动实时双语同传翻译系统")
            print("=" * 50)
            
            # 显示系统信息
            self.show_system_info()
            
            # 运行GUI主循环
            self.subtitle_display.run()
            
        except KeyboardInterrupt:
            print("\n用户中断程序")
        except Exception as e:
            print(f"程序运行错误: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def show_system_info(self):
        """显示系统信息"""
        print(f"配置文件: {self.config_file}")
        print(f"音频采样率: {self.config['audio_settings']['sample_rate']} Hz")
        print(f"翻译模型: {self.config['translation_settings']['model']}")
        print(f"支持语言: 中文 (Chinese) ↔ 西班牙语 (Spanish)")
        print("=" * 50)
        print("使用说明:")
        print("1. 点击'开始录音'开始实时翻译")
        print("2. 对着麦克风说话，系统会自动识别语言并翻译")
        print("3. 翻译结果会实时显示在双屏字幕区域")
        print("4. 可以保存翻译记录，调整字体大小等")
        print("5. 点击'停止录音'停止翻译")
        print("=" * 50)
    
    def cleanup(self):
        """清理资源"""
        print("正在清理系统资源...")
        
        try:
            self.stop_translation()
            
            if self.audio_capture:
                self.audio_capture.cleanup()
            
            if self.subtitle_display:
                self.subtitle_display.destroy()
                
        except Exception as e:
            print(f"清理资源时出错: {e}")
        
        print("系统资源清理完成")

def check_dependencies():
    """检查依赖项"""
    print("检查系统依赖...")
    
    required_modules = [
        'pyaudio',
        'speech_recognition',
        'openai',
        'tkinter'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'tkinter':
                import tkinter
            else:
                __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (缺失)")
            missing_modules.append(module)
    
    if missing_modules:
        print("\n缺失的依赖项:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    print("✓ 所有依赖项检查通过")
    return True

def main():
    """主函数"""
    print("实时双语同传翻译系统")
    print("支持中文 ↔ 西班牙语实时翻译")
    print("=" * 50)
    
    # 检查依赖项
    if not check_dependencies():
        sys.exit(1)
    
    # 检查配置文件
    config_file = "config.json"
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        sys.exit(1)
    
    try:
        # 创建并运行翻译系统
        system = RealTimeTranslationSystem(config_file)
        system.run()
        
    except Exception as e:
        print(f"系统启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()