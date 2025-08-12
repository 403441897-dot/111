#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时墨西哥西班牙语与中文同传翻译程序
支持实时语音识别、ChatGPT翻译和双屏字幕显示
"""

import os
import sys
import time
import threading
import queue
import json
from typing import Optional, Tuple
import logging

# 第三方库导入
try:
    import speech_recognition as sr
    import pygame
    import numpy as np
    import sounddevice as sd
    from openai import OpenAI
    from dotenv import load_dotenv
except ImportError as e:
    print(f"缺少必要的依赖包: {e}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealTimeTranslator:
    """实时翻译器主类"""
    
    def __init__(self):
        self.setup_config()
        self.setup_openai()
        self.setup_audio()
        self.setup_display()
        self.setup_queues()
        self.running = False
        
    def setup_config(self):
        """设置配置参数"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("请在.env文件中设置OPENAI_API_KEY")
            
        self.language_zh = os.getenv('LANGUAGE_ZH', 'zh-CN')
        self.language_es = os.getenv('LANGUAGE_ES', 'es-ES')
        self.window_width = int(os.getenv('WINDOW_WIDTH', 1920))
        self.window_height = int(os.getenv('WINDOW_HEIGHT', 1080))
        self.font_size = int(os.getenv('FONT_SIZE', 48))
        
    def setup_openai(self):
        """设置OpenAI客户端"""
        try:
            self.client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            raise
            
    def setup_audio(self):
        """设置音频相关"""
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # 获取麦克风
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("麦克风初始化成功")
        except Exception as e:
            logger.error(f"麦克风初始化失败: {e}")
            raise
            
    def setup_display(self):
        """设置显示界面"""
        try:
            pygame.init()
            pygame.display.set_caption("实时同传翻译 - 中文 ↔ 西班牙语")
            
            # 创建全屏窗口
            self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.FULLSCREEN)
            
            # 设置字体
            try:
                self.font_zh = pygame.font.Font("NotoSansCJK-Regular.ttc", self.font_size)
            except:
                self.font_zh = pygame.font.SysFont("simsun", self.font_size)
                
            try:
                self.font_es = pygame.font.Font("NotoSans-Regular.ttf", self.font_size)
            except:
                self.font_es = pygame.font.SysFont("arial", self.font_size)
                
            # 颜色定义
            self.colors = {
                'background': (0, 0, 0),
                'text_zh': (255, 255, 255),
                'text_es': (0, 255, 0),
                'border': (100, 100, 100)
            }
            
            logger.info("显示界面初始化成功")
        except Exception as e:
            logger.error(f"显示界面初始化失败: {e}")
            raise
            
    def setup_queues(self):
        """设置队列"""
        self.audio_queue = queue.Queue()
        self.translation_queue = queue.Queue()
        self.display_queue = queue.Queue()
        
    def detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 简单的语言检测逻辑
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        spanish_chars = sum(1 for char in text.lower() if char in 'áéíóúñü')
        
        if chinese_chars > len(text) * 0.3:
            return 'zh'
        elif spanish_chars > 0 or any(word in text.lower() for word in ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'si', 'pero', 'mi', 'su', 'al', 'como', 'han', 'por', 'sus', 'para', 'son', 'con', 'todo', 'esta', 'mas', 'hasta', 'hay', 'donde', 'han', 'quien', 'estan', 'estado', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mi', 'antes', 'algunos', 'que', 'unos', 'yo', 'otro', 'otras', 'otra', 'el', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros']):
            return 'es'
        else:
            # 默认假设为西班牙语输入
            return 'es'
            
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """使用ChatGPT翻译文本"""
        try:
            # 构建翻译提示
            if source_lang == 'zh':
                source_name = "中文"
                target_name = "墨西哥西班牙语"
            else:
                source_name = "墨西哥西班牙语"
                target_name = "中文"
                
            prompt = f"""请将以下{source_name}文本翻译成{target_name}。要求：
1. 保持原意准确
2. 使用自然流畅的表达
3. 如果是墨西哥西班牙语，请使用墨西哥地区的常用表达方式
4. 只返回翻译结果，不要其他解释

原文：{text}

翻译："""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译专家，精通中文和墨西哥西班牙语。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            translation = response.choices[0].message.content.strip()
            logger.info(f"翻译完成: {text} -> {translation}")
            return translation
            
        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return f"[翻译错误: {e}]"
            
    def audio_listener(self):
        """音频监听线程"""
        logger.info("开始音频监听...")
        
        while self.running:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    
                # 将音频数据放入队列
                self.audio_queue.put(audio)
                
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.error(f"音频监听错误: {e}")
                time.sleep(0.1)
                
    def speech_recognizer(self):
        """语音识别线程"""
        logger.info("开始语音识别...")
        
        while self.running:
            try:
                if not self.audio_queue.empty():
                    audio = self.audio_queue.get(timeout=0.1)
                    
                    # 尝试识别中文
                    try:
                        text_zh = self.recognizer.recognize_google(audio, language=self.language_zh)
                        if text_zh.strip():
                            self.process_recognized_text(text_zh, 'zh')
                            continue
                    except sr.UnknownValueError:
                        pass
                        
                    # 尝试识别西班牙语
                    try:
                        text_es = self.recognizer.recognize_google(audio, language=self.language_es)
                        if text_es.strip():
                            self.process_recognized_text(text_es, 'es')
                            continue
                    except sr.UnknownValueError:
                        pass
                        
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"语音识别错误: {e}")
                time.sleep(0.1)
                
    def process_recognized_text(self, text: str, source_lang: str):
        """处理识别的文本"""
        logger.info(f"识别到{source_lang}文本: {text}")
        
        # 确定目标语言
        target_lang = 'zh' if source_lang == 'es' else 'es'
        
        # 将翻译任务放入队列
        self.translation_queue.put({
            'source_text': text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'timestamp': time.time()
        })
        
    def translation_worker(self):
        """翻译工作线程"""
        logger.info("开始翻译工作...")
        
        while self.running:
            try:
                if not self.translation_queue.empty():
                    task = self.translation_queue.get(timeout=0.1)
                    
                    # 执行翻译
                    translation = self.translate_text(
                        task['source_text'],
                        task['source_lang'],
                        task['target_lang']
                    )
                    
                    # 将结果放入显示队列
                    self.display_queue.put({
                        'source_text': task['source_text'],
                        'translation': translation,
                        'source_lang': task['source_lang'],
                        'target_lang': task['target_lang'],
                        'timestamp': task['timestamp']
                    })
                    
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"翻译工作错误: {e}")
                time.sleep(0.1)
                
    def display_manager(self):
        """显示管理线程"""
        logger.info("开始显示管理...")
        
        subtitle_history = []
        max_subtitles = 10
        
        while self.running:
            try:
                # 处理新翻译结果
                if not self.display_queue.empty():
                    result = self.display_queue.get(timeout=0.1)
                    
                    subtitle = {
                        'source_text': result['source_text'],
                        'translation': result['translation'],
                        'source_lang': result['source_lang'],
                        'target_lang': result['target_lang'],
                        'timestamp': result['timestamp']
                    }
                    
                    subtitle_history.append(subtitle)
                    
                    # 保持历史记录数量
                    if len(subtitle_history) > max_subtitles:
                        subtitle_history.pop(0)
                        
                # 更新显示
                self.update_display(subtitle_history)
                
                time.sleep(0.1)
                
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"显示管理错误: {e}")
                time.sleep(0.1)
                
    def update_display(self, subtitles):
        """更新显示内容"""
        try:
            # 清空屏幕
            self.screen.fill(self.colors['background'])
            
            # 绘制标题
            title_font = pygame.font.SysFont("arial", 72)
            title_zh = title_font.render("实时同传翻译 - 中文 ↔ 西班牙语", True, (255, 255, 255))
            title_rect = title_zh.get_rect(center=(self.window_width // 2, 50))
            self.screen.blit(title_zh, title_rect)
            
            # 绘制分隔线
            pygame.draw.line(self.screen, self.colors['border'], 
                           (0, 120), (self.window_width, 120), 3)
            
            # 绘制字幕历史
            y_offset = 150
            for i, subtitle in enumerate(subtitles):
                # 源文本
                if subtitle['source_lang'] == 'zh':
                    source_text = f"中文: {subtitle['source_text']}"
                    source_color = self.colors['text_zh']
                else:
                    source_text = f"Español: {subtitle['source_text']}"
                    source_color = self.colors['text_es']
                    
                source_surface = self.font_zh.render(source_text, True, source_color)
                self.screen.blit(source_surface, (50, y_offset))
                
                # 翻译文本
                if subtitle['target_lang'] == 'zh':
                    target_text = f"翻译: {subtitle['translation']}"
                    target_color = self.colors['text_zh']
                else:
                    target_text = f"Traducción: {subtitle['translation']}"
                    target_color = self.colors['text_es']
                    
                target_surface = self.font_zh.render(target_text, True, target_color)
                self.screen.blit(target_surface, (50, y_offset + 60))
                
                # 时间戳
                time_text = time.strftime("%H:%M:%S", time.localtime(subtitle['timestamp']))
                time_surface = pygame.font.SysFont("arial", 24).render(time_text, True, (150, 150, 150))
                self.screen.blit(time_surface, (self.window_width - 150, y_offset))
                
                y_offset += 140
                
                # 绘制分隔线
                if i < len(subtitles) - 1:
                    pygame.draw.line(self.screen, (50, 50, 50), 
                                   (50, y_offset - 10), (self.window_width - 50, y_offset - 10), 1)
                    
            # 绘制底部信息
            info_text = "按ESC键退出程序 | 按空格键暂停/恢复"
            info_surface = pygame.font.SysFont("arial", 24).render(info_text, True, (150, 150, 150))
            info_rect = info_surface.get_rect(center=(self.window_width // 2, self.window_height - 30))
            self.screen.blit(info_surface, info_rect)
            
            # 更新显示
            pygame.display.flip()
            
        except Exception as e:
            logger.error(f"显示更新错误: {e}")
            
    def handle_events(self):
        """处理用户事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    # 暂停/恢复功能
                    pass
        return True
        
    def run(self):
        """运行主程序"""
        logger.info("启动实时同传翻译程序...")
        
        try:
            self.running = True
            
            # 启动工作线程
            threads = []
            
            audio_thread = threading.Thread(target=self.audio_listener, daemon=True)
            threads.append(audio_thread)
            
            recognition_thread = threading.Thread(target=self.speech_recognizer, daemon=True)
            threads.append(recognition_thread)
            
            translation_thread = threading.Thread(target=self.translation_worker, daemon=True)
            threads.append(translation_thread)
            
            display_thread = threading.Thread(target=self.display_manager, daemon=True)
            threads.append(display_thread)
            
            # 启动所有线程
            for thread in threads:
                thread.start()
                
            logger.info("所有工作线程已启动")
            
            # 主事件循环
            while self.running:
                if not self.handle_events():
                    break
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        except Exception as e:
            logger.error(f"程序运行错误: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理资源...")
        self.running = False
        
        # 等待线程结束
        time.sleep(1)
        
        # 清理pygame
        pygame.quit()
        
        logger.info("程序已退出")

def main():
    """主函数"""
    try:
        translator = RealTimeTranslator()
        translator.run()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()