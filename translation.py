from openai import OpenAI
import json
import threading
import queue
import time
from typing import Dict, Optional

class ChatGPTTranslator:
    def __init__(self, config_file="config.json"):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.api_key = config['openai_api_key']
        self.translation_settings = config['translation_settings']
        
        # 初始化OpenAI客户端
        self.client = OpenAI(api_key=self.api_key)
        
        # 翻译提示模板
        self.translation_prompts = {
            'chinese_to_spanish': {
                'system': "你是一位专业的中文到西班牙语同声传译专家。请提供准确、自然、符合语境的翻译。保持原文的语调和意图。对于专业术语，请使用最准确的西班牙语表达。",
                'user_template': "请将以下中文翻译成西班牙语：\n\n{text}\n\n翻译："
            },
            'spanish_to_chinese': {
                'system': "你是一位专业的西班牙语到中文同声传译专家。请提供准确、自然、符合语境的翻译。保持原文的语调和意图。对于专业术语，请使用最准确的中文表达。",
                'user_template': "请将以下西班牙语翻译成中文：\n\n{text}\n\n翻译："
            }
        }
    
    def detect_language(self, text: str) -> str:
        """检测文本语言"""
        if not text:
            return 'unknown'
        
        # 检测中文字符
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return 'unknown'
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return 'chinese'
        else:
            return 'spanish'
    
    def translate_text(self, text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> Dict:
        """翻译文本"""
        if not text or not text.strip():
            return {'error': '文本为空'}
        
        # 自动检测源语言
        if source_lang is None:
            source_lang = self.detect_language(text)
        
        # 根据源语言确定目标语言
        if source_lang == 'chinese':
            direction = 'chinese_to_spanish'
            detected_target = 'spanish'
        elif source_lang == 'spanish':
            direction = 'spanish_to_chinese'
            detected_target = 'chinese'
        else:
            return {'error': f'不支持的源语言: {source_lang}'}
        
        # 如果指定了目标语言，验证是否匹配
        if target_lang and target_lang != detected_target:
            return {'error': f'源语言 {source_lang} 与目标语言 {target_lang} 不匹配'}
        
        try:
            prompt = self.translation_prompts[direction]
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.translation_settings['model'],
                messages=[
                    {
                        "role": "system",
                        "content": prompt['system']
                    },
                    {
                        "role": "user", 
                        "content": prompt['user_template'].format(text=text)
                    }
                ],
                max_tokens=self.translation_settings['max_tokens'],
                temperature=self.translation_settings['temperature'],
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            translation = response.choices[0].message.content.strip()
            
            return {
                'original_text': text,
                'translated_text': translation,
                'source_language': source_lang,
                'target_language': detected_target,
                'direction': direction,
                'success': True
            }
            
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower():
                return {'error': 'OpenAI API认证失败，请检查API密钥'}
            elif "rate_limit" in error_msg.lower() or "quota" in error_msg.lower():
                return {'error': 'API调用频率限制或配额不足，请稍后再试'}
            else:
                return {'error': f'翻译错误: {error_msg}'}
    
    def translate_chinese_to_spanish(self, text: str) -> Dict:
        """中文翻译为西班牙语"""
        return self.translate_text(text, source_lang='chinese', target_lang='spanish')
    
    def translate_spanish_to_chinese(self, text: str) -> Dict:
        """西班牙语翻译为中文"""
        return self.translate_text(text, source_lang='spanish', target_lang='chinese')

class TranslationService:
    """翻译服务类，支持异步翻译"""
    
    def __init__(self, config_file="config.json"):
        self.translator = ChatGPTTranslator(config_file)
        self.translation_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_thread = None
        self.is_running = False
        
        # 翻译缓存
        self.translation_cache = {}
        self.cache_max_size = 100
    
    def start_service(self):
        """启动翻译服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_translation)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        print("翻译服务已启动")
    
    def stop_service(self):
        """停止翻译服务"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()
        print("翻译服务已停止")
    
    def add_text_for_translation(self, text: str, source_lang: Optional[str] = None):
        """添加文本到翻译队列"""
        if not text or not text.strip():
            return
        
        # 检查缓存
        cache_key = f"{text}_{source_lang}"
        if cache_key in self.translation_cache:
            cached_result = self.translation_cache[cache_key]
            cached_result['from_cache'] = True
            self.result_queue.put(cached_result)
            return
        
        # 添加到翻译队列
        self.translation_queue.put((text, source_lang, time.time()))
    
    def get_translation_result(self):
        """获取翻译结果"""
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None
    
    def _process_translation(self):
        """处理翻译队列中的文本"""
        while self.is_running:
            try:
                text, source_lang, timestamp = self.translation_queue.get(timeout=1)
                
                # 执行翻译
                result = self.translator.translate_text(text, source_lang)
                result['timestamp'] = timestamp
                result['from_cache'] = False
                
                # 添加到缓存
                if result.get('success'):
                    cache_key = f"{text}_{source_lang}"
                    self.translation_cache[cache_key] = result.copy()
                    
                    # 限制缓存大小
                    if len(self.translation_cache) > self.cache_max_size:
                        # 删除最旧的缓存项
                        oldest_key = min(self.translation_cache.keys())
                        del self.translation_cache[oldest_key]
                
                # 添加到结果队列
                self.result_queue.put(result)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"翻译处理错误: {e}")
    
    def clear_cache(self):
        """清除翻译缓存"""
        self.translation_cache.clear()
        print("翻译缓存已清除")

class BatchTranslator:
    """批量翻译类"""
    
    def __init__(self, config_file="config.json"):
        self.translator = ChatGPTTranslator(config_file)
    
    def translate_batch(self, texts: list, source_lang: Optional[str] = None) -> list:
        """批量翻译文本"""
        results = []
        
        for text in texts:
            if text and text.strip():
                result = self.translator.translate_text(text, source_lang)
                results.append(result)
            else:
                results.append({'error': '文本为空'})
        
        return results
    
    def translate_file(self, input_file: str, output_file: str, source_lang: Optional[str] = None):
        """翻译文件"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            translated_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    result = self.translator.translate_text(line, source_lang)
                    if result.get('success'):
                        translated_lines.append(result['translated_text'])
                    else:
                        translated_lines.append(f"[翻译失败: {result.get('error', '未知错误')}]")
                else:
                    translated_lines.append("")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(translated_lines))
            
            print(f"文件翻译完成: {input_file} -> {output_file}")
            
        except Exception as e:
            print(f"文件翻译错误: {e}")

if __name__ == "__main__":
    # 测试翻译功能
    translator = ChatGPTTranslator()
    
    # 测试中文翻译
    chinese_text = "你好，今天天气很好。"
    result = translator.translate_chinese_to_spanish(chinese_text)
    print(f"中文: {chinese_text}")
    print(f"西班牙语: {result}")
    
    # 测试西班牙语翻译
    spanish_text = "Hola, ¿cómo estás?"
    result = translator.translate_spanish_to_chinese(spanish_text)
    print(f"西班牙语: {spanish_text}")
    print(f"中文: {result}")