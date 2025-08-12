#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 实时同传翻译程序
"""

import os
from typing import Dict, Any

class Config:
    """配置管理类"""
    
    def __init__(self):
        self.load_config()
        
    def load_config(self):
        """加载配置"""
        # OpenAI API配置
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.openai_api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4')
        
        # 语音识别配置
        self.language_zh = os.getenv('LANGUAGE_ZH', 'zh-CN')
        self.language_es = os.getenv('LANGUAGE_ES', 'es-ES')
        self.energy_threshold = int(os.getenv('ENERGY_THRESHOLD', 4000))
        self.pause_threshold = float(os.getenv('PAUSE_THRESHOLD', 0.8))
        self.phrase_time_limit = int(os.getenv('PHRASE_TIME_LIMIT', 10))
        
        # 显示配置
        self.window_width = int(os.getenv('WINDOW_WIDTH', 1920))
        self.window_height = int(os.getenv('WINDOW_HEIGHT', 1080))
        self.font_size = int(os.getenv('FONT_SIZE', 48))
        self.max_subtitles = int(os.getenv('MAX_SUBTITLES', 10))
        
        # 音频配置
        self.sample_rate = int(os.getenv('SAMPLE_RATE', 16000))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 1024))
        
        # 翻译配置
        self.translation_timeout = int(os.getenv('TRANSLATION_TIMEOUT', 30))
        self.max_tokens = int(os.getenv('MAX_TOKENS', 500))
        self.temperature = float(os.getenv('TEMPERATURE', 0.3))
        
        # 颜色配置
        self.colors = {
            'background': (0, 0, 0),
            'text_zh': (255, 255, 255),
            'text_es': (0, 255, 0),
            'border': (100, 100, 100),
            'title': (255, 255, 255),
            'timestamp': (150, 150, 150),
            'info': (150, 150, 150)
        }
        
    def validate(self) -> bool:
        """验证配置"""
        if not self.openai_api_key:
            print("错误: 请在.env文件中设置OPENAI_API_KEY")
            return False
            
        if self.window_width <= 0 or self.window_height <= 0:
            print("错误: 窗口尺寸必须大于0")
            return False
            
        if self.font_size <= 0:
            print("错误: 字体大小必须大于0")
            return False
            
        return True
        
    def get_display_config(self) -> Dict[str, Any]:
        """获取显示配置"""
        return {
            'width': self.window_width,
            'height': self.window_height,
            'font_size': self.font_size,
            'max_subtitles': self.max_subtitles,
            'colors': self.colors
        }
        
    def get_audio_config(self) -> Dict[str, Any]:
        """获取音频配置"""
        return {
            'energy_threshold': self.energy_threshold,
            'pause_threshold': self.pause_threshold,
            'phrase_time_limit': self.phrase_time_limit,
            'sample_rate': self.sample_rate,
            'chunk_size': self.chunk_size
        }
        
    def get_translation_config(self) -> Dict[str, Any]:
        """获取翻译配置"""
        return {
            'api_key': self.openai_api_key,
            'api_base': self.openai_api_base,
            'model': self.openai_model,
            'timeout': self.translation_timeout,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }
        
    def print_config(self):
        """打印当前配置"""
        print("=== 实时同传翻译程序配置 ===")
        print(f"OpenAI模型: {self.openai_model}")
        print(f"窗口尺寸: {self.window_width}x{self.window_height}")
        print(f"字体大小: {self.font_size}")
        print(f"最大字幕数: {self.max_subtitles}")
        print(f"语音识别阈值: {self.energy_threshold}")
        print(f"暂停阈值: {self.pause_threshold}秒")
        print(f"短语时间限制: {self.phrase_time_limit}秒")
        print("================================")