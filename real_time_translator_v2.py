#!/usr/bin/env python3
"""
实时语音翻译程序 V2
支持中文和西班牙语双向同声传译，带双屏字幕显示
使用最新的OpenAI API和改进的音频处理
"""

import os
import sys
import threading
import queue
import time
import json
from datetime import datetime
import speech_recognition as sr
from openai import OpenAI
import pygame
import numpy as np
import pyaudio
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import configparser
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
import webrtcvad


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TranslationItem:
    """翻译项数据类"""
    timestamp: str
    source_text: str
    target_text: Optional[str] = None
    source_lang: str = 'zh-CN'
    target_lang: str = 'es'


class AudioProcessor:
    """音频处理器，提供更好的语音活动检测"""
    
    def __init__(self, sample_rate=16000, frame_duration_ms=30):
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.vad = webrtcvad.Vad(2)  # 灵敏度级别 0-3
        
    def is_speech(self, audio_frame):
        """检测音频帧是否包含语音"""
        return self.vad.is_speech(audio_frame, self.sample_rate)


class RealTimeTranslatorV2:
    def __init__(self):
        """初始化翻译器"""
        self.config = self.load_config()
        self.setup_openai()
        
        # 初始化语音识别器
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=16000)
        
        # 初始化音频处理器
        self.audio_processor = AudioProcessor()
        
        # 初始化队列
        self.audio_queue = queue.Queue(maxsize=100)
        self.translation_queue = queue.Queue(maxsize=100)
        self.display_queue = queue.Queue(maxsize=100)
        
        # 语言设置
        self.source_lang = 'zh-CN'
        self.target_lang = 'es'
        self.lang_names = {
            'zh-CN': '中文',
            'es': '西班牙语'
        }
        
        # 控制标志
        self.is_running = False
        self.is_paused = False
        
        # 翻译历史
        self.translation_history = []
        
        # 初始化GUI
        self.init_gui()
        
    def load_config(self):
        """加载配置文件"""
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        
        if not os.path.exists(config_file):
            # 创建默认配置
            config['API'] = {
                'openai_key': os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here'),
                'openai_base_url': 'https://api.openai.com/v1'
            }
            config['Audio'] = {
                'sample_rate': '16000',
                'chunk_size': '1024',
                'energy_threshold': '2000',
                'pause_threshold': '0.8',
                'phrase_threshold': '0.3',
                'max_phrase_duration': '5'
            }
            config['Translation'] = {
                'model': 'gpt-4-turbo-preview',
                'temperature': '0.3',
                'max_tokens': '500'
            }
            config['Display'] = {
                'font_size_source': '14',
                'font_size_target': '14',
                'window_width': '1400',
                'window_height': '800'
            }
            
            with open(config_file, 'w') as f:
                config.write(f)
                
        config.read(config_file)
        return config
        
    def setup_openai(self):
        """设置OpenAI客户端"""
        api_key = self.config.get('API', 'openai_key')
        if api_key == 'your-openai-api-key-here':
            api_key = os.getenv('OPENAI_API_KEY')
            
        if not api_key:
            logger.warning("未找到OpenAI API密钥")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(
                api_key=api_key,
                base_url=self.config.get('API', 'openai_base_url', fallback='https://api.openai.com/v1')
            )
            
    def init_gui(self):
        """初始化双屏GUI界面"""
        self.root = tk.Tk()
        self.root.title("实时同声传译系统 V2")
        
        # 获取配置的窗口大小
        width = self.config.getint('Display', 'window_width', fallback=1400)
        height = self.config.getint('Display', 'window_height', fallback=800)
        self.root.geometry(f"{width}x{height}")
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建控制面板
        self.create_control_panel(main_frame)
        
        # 创建双屏显示区域
        self.create_display_area(main_frame)
        
        # 创建状态栏
        self.create_status_bar(main_frame)
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 绑定快捷键
        self.root.bind('<F1>', lambda e: self.start_translation())
        self.root.bind('<F2>', lambda e: self.pause_translation())
        self.root.bind('<F3>', lambda e: self.stop_translation())
        self.root.bind('<F4>', lambda e: self.switch_languages())
        
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 按钮行
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, columnspan=4)
        
        self.start_button = ttk.Button(
            button_frame, text="▶ 开始翻译 (F1)", 
            command=self.start_translation, 
            style='Accent.TButton'
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(
            button_frame, text="⏸ 暂停 (F2)", 
            command=self.pause_translation, 
            state=tk.DISABLED
        )
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame, text="⏹ 停止 (F3)", 
            command=self.stop_translation, 
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=2, padx=5)
        
        # 语言设置
        lang_frame = ttk.Frame(control_frame)
        lang_frame.grid(row=0, column=1, padx=20)
        
        ttk.Label(lang_frame, text="源语言:").grid(row=0, column=0, padx=5)
        self.source_lang_label = ttk.Label(
            lang_frame, 
            text=self.lang_names[self.source_lang],
            font=('Arial', 10, 'bold')
        )
        self.source_lang_label.grid(row=0, column=1, padx=5)
        
        ttk.Label(lang_frame, text="→").grid(row=0, column=2, padx=5)
        
        ttk.Label(lang_frame, text="目标语言:").grid(row=0, column=3, padx=5)
        self.target_lang_label = ttk.Label(
            lang_frame, 
            text=self.lang_names[self.target_lang],
            font=('Arial', 10, 'bold')
        )
        self.target_lang_label.grid(row=0, column=4, padx=5)
        
        self.lang_switch_button = ttk.Button(
            lang_frame, text="🔄 切换方向 (F4)", 
            command=self.switch_languages
        )
        self.lang_switch_button.grid(row=0, column=5, padx=10)
        
        # 设置按钮
        settings_frame = ttk.Frame(control_frame)
        settings_frame.grid(row=0, column=2, padx=20)
        
        self.clear_button = ttk.Button(
            settings_frame, text="🗑 清空显示", 
            command=self.clear_display
        )
        self.clear_button.grid(row=0, column=0, padx=5)
        
        self.export_button = ttk.Button(
            settings_frame, text="💾 导出记录", 
            command=self.export_history
        )
        self.export_button.grid(row=0, column=1, padx=5)
        
    def create_display_area(self, parent):
        """创建双屏显示区域"""
        display_frame = ttk.Frame(parent)
        display_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置列权重
        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
        # 左屏 - 源语言
        left_frame = ttk.LabelFrame(
            display_frame, 
            text=f"源语言 ({self.lang_names[self.source_lang]})", 
            padding="10"
        )
        left_frame.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.left_frame = left_frame
        
        # 源语言文本显示
        font_size = self.config.getint('Display', 'font_size_source', fallback=14)
        self.source_text = scrolledtext.ScrolledText(
            left_frame, 
            width=50, 
            height=25,
            font=('Microsoft YaHei', font_size),
            wrap=tk.WORD,
            bg='#f8f9fa',
            fg='#212529'
        )
        self.source_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # 右屏 - 目标语言
        right_frame = ttk.LabelFrame(
            display_frame, 
            text=f"目标语言 ({self.lang_names[self.target_lang]})",
            padding="10"
        )
        right_frame.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.right_frame = right_frame
        
        # 目标语言文本显示
        font_size = self.config.getint('Display', 'font_size_target', fallback=14)
        self.target_text = scrolledtext.ScrolledText(
            right_frame, 
            width=50, 
            height=25,
            font=('Arial', font_size),
            wrap=tk.WORD,
            bg='#f8f9fa',
            fg='#212529'
        )
        self.target_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # 设置标签样式
        self.source_text.tag_configure('timestamp', foreground='#6c757d', font=('Arial', 10))
        self.target_text.tag_configure('timestamp', foreground='#6c757d', font=('Arial', 10))
        
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 状态标签
        self.status_label = ttk.Label(status_frame, text="状态: 就绪", font=('Arial', 10))
        self.status_label.grid(row=0, column=0, padx=10)
        
        # 音频级别指示器
        self.audio_level_label = ttk.Label(status_frame, text="音频: ▁▁▁▁▁", font=('Arial', 10))
        self.audio_level_label.grid(row=0, column=1, padx=10)
        
        # 翻译计数
        self.translation_count_label = ttk.Label(status_frame, text="翻译数: 0", font=('Arial', 10))
        self.translation_count_label.grid(row=0, column=2, padx=10)
        
        # API状态
        api_status = "已连接" if self.openai_client else "未连接"
        self.api_status_label = ttk.Label(status_frame, text=f"API: {api_status}", font=('Arial', 10))
        self.api_status_label.grid(row=0, column=3, padx=10)
        
    def start_translation(self):
        """开始翻译"""
        if not self.openai_client:
            messagebox.showerror("错误", "请先配置OpenAI API密钥")
            return
            
        self.is_running = True
        self.is_paused = False
        
        # 更新按钮状态
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("正在录音...")
        
        # 启动工作线程
        threading.Thread(target=self.audio_capture_thread, daemon=True).start()
        threading.Thread(target=self.speech_recognition_thread, daemon=True).start()
        threading.Thread(target=self.translation_thread, daemon=True).start()
        threading.Thread(target=self.display_update_thread, daemon=True).start()
        
        logger.info("翻译服务已启动")
        
    def pause_translation(self):
        """暂停/继续翻译"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.config(text="▶ 继续 (F2)")
            self.update_status("已暂停")
        else:
            self.pause_button.config(text="⏸ 暂停 (F2)")
            self.update_status("正在录音...")
            
    def stop_translation(self):
        """停止翻译"""
        self.is_running = False
        self.is_paused = False
        
        # 更新按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="⏸ 暂停 (F2)")
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("已停止")
        
        logger.info("翻译服务已停止")
        
    def switch_languages(self):
        """切换源语言和目标语言"""
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        
        # 更新标签
        self.source_lang_label.config(text=self.lang_names[self.source_lang])
        self.target_lang_label.config(text=self.lang_names[self.target_lang])
        
        # 更新框架标签
        self.left_frame.config(text=f"源语言 ({self.lang_names[self.source_lang]})")
        self.right_frame.config(text=f"目标语言 ({self.lang_names[self.target_lang]})")
        
        logger.info(f"语言切换: {self.source_lang} -> {self.target_lang}")
        
    def clear_display(self):
        """清空显示内容"""
        self.source_text.delete(1.0, tk.END)
        self.target_text.delete(1.0, tk.END)
        logger.info("显示内容已清空")
        
    def export_history(self):
        """导出翻译历史"""
        if not self.translation_history:
            messagebox.showinfo("提示", "没有可导出的翻译记录")
            return
            
        filename = f"translation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.translation_history, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"翻译记录已导出到: {filename}")
            logger.info(f"翻译记录已导出: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
            logger.error(f"导出失败: {e}")
            
    def update_status(self, status):
        """更新状态栏"""
        self.status_label.config(text=f"状态: {status}")
        
    def update_audio_level(self, level):
        """更新音频级别显示"""
        bars = int(level * 5)
        display = "▁" * (5 - bars) + "▃" * bars
        self.audio_level_label.config(text=f"音频: {display}")
        
    def audio_capture_thread(self):
        """音频捕获线程"""
        try:
            # 调整环境噪音
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("环境噪音调整完成")
                
            # 设置识别参数
            self.recognizer.energy_threshold = self.config.getint('Audio', 'energy_threshold', fallback=2000)
            self.recognizer.pause_threshold = self.config.getfloat('Audio', 'pause_threshold', fallback=0.8)
            self.recognizer.phrase_threshold = self.config.getfloat('Audio', 'phrase_threshold', fallback=0.3)
            
            while self.is_running:
                if not self.is_paused:
                    try:
                        with self.microphone as source:
                            # 监听音频
                            audio = self.recognizer.listen(
                                source, 
                                timeout=1,
                                phrase_time_limit=self.config.getint('Audio', 'max_phrase_duration', fallback=5)
                            )
                            
                            # 更新音频级别
                            rms = np.sqrt(np.mean(np.frombuffer(audio.frame_data, dtype=np.int16)**2))
                            level = min(1.0, rms / 32768)
                            self.root.after(0, self.update_audio_level, level)
                            
                            # 将音频加入队列
                            if not self.audio_queue.full():
                                self.audio_queue.put(audio)
                                
                    except sr.WaitTimeoutError:
                        pass
                    except Exception as e:
                        logger.error(f"音频捕获错误: {e}")
                else:
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"音频捕获线程错误: {e}")
            self.root.after(0, self.stop_translation)
            
    def speech_recognition_thread(self):
        """语音识别线程"""
        while self.is_running:
            try:
                if not self.audio_queue.empty():
                    audio = self.audio_queue.get(timeout=1)
                    
                    # 识别语音
                    try:
                        # 根据源语言选择识别语言
                        if self.source_lang == 'zh-CN':
                            text = self.recognizer.recognize_google(audio, language='zh-CN')
                        else:
                            text = self.recognizer.recognize_google(audio, language='es-ES')
                            
                        if text:
                            # 创建翻译项
                            item = TranslationItem(
                                timestamp=datetime.now().strftime("%H:%M:%S"),
                                source_text=text,
                                source_lang=self.source_lang,
                                target_lang=self.target_lang
                            )
                            
                            # 加入翻译队列
                            if not self.translation_queue.full():
                                self.translation_queue.put(item)
                                
                            logger.info(f"识别到文本: {text}")
                            
                    except sr.UnknownValueError:
                        logger.debug("无法识别语音")
                    except sr.RequestError as e:
                        logger.error(f"语音识别请求错误: {e}")
                        
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"语音识别线程错误: {e}")
                
            time.sleep(0.1)
            
    def translation_thread(self):
        """翻译线程"""
        while self.is_running:
            try:
                if not self.translation_queue.empty():
                    item = self.translation_queue.get(timeout=1)
                    
                    # 使用OpenAI进行翻译
                    translation = self.translate_with_openai(item.source_text, item.source_lang, item.target_lang)
                    
                    if translation:
                        item.target_text = translation
                        
                        # 添加到历史记录
                        self.translation_history.append({
                            'timestamp': item.timestamp,
                            'source': item.source_text,
                            'target': item.target_text,
                            'source_lang': item.source_lang,
                            'target_lang': item.target_lang
                        })
                        
                        # 加入显示队列
                        if not self.display_queue.full():
                            self.display_queue.put(item)
                            
                        # 更新翻译计数
                        count = len(self.translation_history)
                        self.root.after(0, lambda: self.translation_count_label.config(text=f"翻译数: {count}"))
                        
                        logger.info(f"翻译完成: {item.source_text} -> {translation}")
                        
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"翻译线程错误: {e}")
                
            time.sleep(0.1)
            
    def display_update_thread(self):
        """显示更新线程"""
        while self.is_running:
            try:
                if not self.display_queue.empty():
                    item = self.display_queue.get(timeout=1)
                    
                    # 更新显示
                    self.root.after(0, self.update_display, item)
                    
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"显示更新线程错误: {e}")
                
            time.sleep(0.1)
            
    def translate_with_openai(self, text, source_lang, target_lang):
        """使用OpenAI API进行翻译"""
        if not self.openai_client:
            return None
            
        try:
            # 构建翻译提示
            lang_map = {
                'zh-CN': '中文',
                'es': '西班牙语'
            }
            
            source_name = lang_map.get(source_lang, source_lang)
            target_name = lang_map.get(target_lang, target_lang)
            
            messages = [
                {
                    "role": "system",
                    "content": f"你是一个专业的{source_name}和{target_name}同声传译专家。请准确、流畅地进行翻译，保持原文的语气和风格。"
                },
                {
                    "role": "user",
                    "content": f"请将以下{source_name}翻译成{target_name}：\n\n{text}"
                }
            ]
            
            # 调用API
            response = self.openai_client.chat.completions.create(
                model=self.config.get('Translation', 'model', fallback='gpt-3.5-turbo'),
                messages=messages,
                temperature=float(self.config.get('Translation', 'temperature', fallback='0.3')),
                max_tokens=int(self.config.get('Translation', 'max_tokens', fallback='500'))
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI翻译错误: {e}")
            return f"[翻译错误] {text}"
            
    def update_display(self, item: TranslationItem):
        """更新显示内容"""
        # 更新源语言显示
        self.source_text.insert(tk.END, f"[{item.timestamp}] ", 'timestamp')
        self.source_text.insert(tk.END, f"{item.source_text}\n\n")
        self.source_text.see(tk.END)
        
        # 更新目标语言显示
        if item.target_text:
            self.target_text.insert(tk.END, f"[{item.timestamp}] ", 'timestamp')
            self.target_text.insert(tk.END, f"{item.target_text}\n\n")
            self.target_text.see(tk.END)
            
    def run(self):
        """运行主程序"""
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 显示欢迎信息
        welcome_msg = """欢迎使用实时同声传译系统 V2！

快捷键：
- F1: 开始翻译
- F2: 暂停/继续
- F3: 停止翻译
- F4: 切换语言方向

请确保已配置OpenAI API密钥。
"""
        self.source_text.insert(tk.END, welcome_msg)
        self.target_text.insert(tk.END, "Welcome to Real-time Translation System V2!\n\n¡Bienvenido al Sistema de Traducción en Tiempo Real V2!")
        
        # 运行主循环
        self.root.mainloop()
        
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            self.stop_translation()
        self.root.destroy()


if __name__ == "__main__":
    # 设置环境变量（如果需要）
    # os.environ['OPENAI_API_KEY'] = 'your-api-key-here'
    
    # 创建并运行翻译器
    translator = RealTimeTranslatorV2()
    translator.run()