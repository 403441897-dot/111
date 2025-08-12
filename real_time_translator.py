#!/usr/bin/env python3
"""
实时语音翻译程序
支持中文和西班牙语双向同声传译，带双屏字幕显示
"""

import os
import sys
import threading
import queue
import time
import json
from datetime import datetime
import speech_recognition as sr
import openai
import pygame
import numpy as np
from googletrans import Translator
import pyaudio
import wave
import tkinter as tk
from tkinter import ttk, scrolledtext
import configparser


class RealTimeTranslator:
    def __init__(self):
        """初始化翻译器"""
        self.config = self.load_config()
        
        # 设置OpenAI API
        openai.api_key = self.config.get('API', 'openai_key', fallback='')
        
        # 初始化语音识别器
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # 初始化翻译队列
        self.audio_queue = queue.Queue()
        self.translation_queue = queue.Queue()
        
        # 语言设置
        self.source_lang = 'zh-CN'  # 中文
        self.target_lang = 'es'     # 西班牙语
        
        # 控制标志
        self.is_running = False
        self.is_paused = False
        
        # 初始化GUI
        self.init_gui()
        
    def load_config(self):
        """加载配置文件"""
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        
        if not os.path.exists(config_file):
            # 创建默认配置
            config['API'] = {
                'openai_key': 'your-openai-api-key-here'
            }
            config['Audio'] = {
                'sample_rate': '16000',
                'chunk_size': '1024',
                'energy_threshold': '4000'
            }
            config['Translation'] = {
                'model': 'gpt-4',
                'temperature': '0.3'
            }
            
            with open(config_file, 'w') as f:
                config.write(f)
                
        config.read(config_file)
        return config
        
    def init_gui(self):
        """初始化双屏GUI界面"""
        self.root = tk.Tk()
        self.root.title("实时同声传译系统")
        self.root.geometry("1200x800")
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="开始翻译", command=self.start_translation)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(control_frame, text="暂停", command=self.pause_translation, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_translation, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=5)
        
        # 语言切换
        self.lang_switch_button = ttk.Button(control_frame, text="切换语言方向", command=self.switch_languages)
        self.lang_switch_button.grid(row=0, column=3, padx=20)
        
        # 状态标签
        self.status_label = ttk.Label(control_frame, text="状态: 就绪")
        self.status_label.grid(row=0, column=4, padx=20)
        
        # 双屏显示区域
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左屏 - 源语言
        left_frame = ttk.LabelFrame(display_frame, text="源语言 (中文)", padding="10")
        left_frame.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.source_text = scrolledtext.ScrolledText(left_frame, width=50, height=30, 
                                                     font=('Microsoft YaHei', 12))
        self.source_text.grid(row=0, column=0)
        
        # 右屏 - 目标语言
        right_frame = ttk.LabelFrame(display_frame, text="目标语言 (西班牙语)", padding="10")
        right_frame.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.target_text = scrolledtext.ScrolledText(right_frame, width=50, height=30,
                                                     font=('Arial', 12))
        self.target_text.grid(row=0, column=0)
        
        # 配置权重以实现响应式布局
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
    def start_translation(self):
        """开始翻译"""
        self.is_running = True
        self.is_paused = False
        
        # 更新按钮状态
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="状态: 正在录音...")
        
        # 启动工作线程
        threading.Thread(target=self.audio_capture_thread, daemon=True).start()
        threading.Thread(target=self.speech_recognition_thread, daemon=True).start()
        threading.Thread(target=self.translation_thread, daemon=True).start()
        
    def pause_translation(self):
        """暂停翻译"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.config(text="继续")
            self.status_label.config(text="状态: 已暂停")
        else:
            self.pause_button.config(text="暂停")
            self.status_label.config(text="状态: 正在录音...")
            
    def stop_translation(self):
        """停止翻译"""
        self.is_running = False
        self.is_paused = False
        
        # 更新按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="暂停")
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="状态: 已停止")
        
    def switch_languages(self):
        """切换源语言和目标语言"""
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        
        # 更新GUI标签
        if self.source_lang == 'zh-CN':
            source_label = "源语言 (中文)"
            target_label = "目标语言 (西班牙语)"
        else:
            source_label = "源语言 (西班牙语)"
            target_label = "目标语言 (中文)"
            
        # 更新框架标签
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for frame in child.winfo_children():
                            if isinstance(frame, ttk.LabelFrame):
                                if "源语言" in frame['text']:
                                    frame.config(text=source_label)
                                elif "目标语言" in frame['text']:
                                    frame.config(text=target_label)
                                    
    def audio_capture_thread(self):
        """音频捕获线程"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            
        while self.is_running:
            if not self.is_paused:
                try:
                    with self.microphone as source:
                        # 设置超时时间，避免长时间阻塞
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"音频捕获错误: {e}")
            else:
                time.sleep(0.1)
                
    def speech_recognition_thread(self):
        """语音识别线程"""
        while self.is_running:
            try:
                if not self.audio_queue.empty():
                    audio = self.audio_queue.get(timeout=1)
                    
                    # 识别语音
                    try:
                        if self.source_lang == 'zh-CN':
                            text = self.recognizer.recognize_google(audio, language='zh-CN')
                        else:
                            text = self.recognizer.recognize_google(audio, language='es-ES')
                            
                        if text:
                            # 添加时间戳
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            
                            # 更新源语言显示
                            self.root.after(0, self.update_source_display, f"[{timestamp}] {text}\n")
                            
                            # 将文本加入翻译队列
                            self.translation_queue.put(text)
                            
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"语音识别错误: {e}")
                        
            except queue.Empty:
                pass
            except Exception as e:
                print(f"识别线程错误: {e}")
                
            time.sleep(0.1)
            
    def translation_thread(self):
        """翻译线程"""
        while self.is_running:
            try:
                if not self.translation_queue.empty():
                    text = self.translation_queue.get(timeout=1)
                    
                    # 使用OpenAI进行翻译
                    translation = self.translate_with_openai(text)
                    
                    if translation:
                        # 添加时间戳
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        # 更新目标语言显示
                        self.root.after(0, self.update_target_display, f"[{timestamp}] {translation}\n")
                        
            except queue.Empty:
                pass
            except Exception as e:
                print(f"翻译线程错误: {e}")
                
            time.sleep(0.1)
            
    def translate_with_openai(self, text):
        """使用OpenAI API进行翻译"""
        try:
            if self.source_lang == 'zh-CN':
                prompt = f"请将以下中文翻译成西班牙语，保持原意和语气：\n{text}"
                system_message = "你是一个专业的中西翻译专家，擅长同声传译。"
            else:
                prompt = f"请将以下西班牙语翻译成中文，保持原意和语气：\n{text}"
                system_message = "你是一个专业的西中翻译专家，擅长同声传译。"
                
            response = openai.ChatCompletion.create(
                model=self.config.get('Translation', 'model', fallback='gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=float(self.config.get('Translation', 'temperature', fallback='0.3')),
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI翻译错误: {e}")
            # 备用翻译方案
            try:
                translator = Translator()
                if self.source_lang == 'zh-CN':
                    result = translator.translate(text, src='zh-cn', dest='es')
                else:
                    result = translator.translate(text, src='es', dest='zh-cn')
                return result.text
            except:
                return f"[翻译失败] {text}"
                
    def update_source_display(self, text):
        """更新源语言显示"""
        self.source_text.insert(tk.END, text)
        self.source_text.see(tk.END)  # 自动滚动到底部
        
    def update_target_display(self, text):
        """更新目标语言显示"""
        self.target_text.insert(tk.END, text)
        self.target_text.see(tk.END)  # 自动滚动到底部
        
    def run(self):
        """运行主程序"""
        self.root.mainloop()


if __name__ == "__main__":
    # 检查必要的环境变量
    if not os.getenv('OPENAI_API_KEY') and not os.path.exists('config.ini'):
        print("警告: 请设置OPENAI_API_KEY环境变量或在config.ini中配置API密钥")
        
    # 创建并运行翻译器
    translator = RealTimeTranslator()
    translator.run()