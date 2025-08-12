import speech_recognition as sr
import json
import threading
import queue
from io import BytesIO
import wave

class SpeechRecognizer:
    def __init__(self, config_file="config.json"):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.audio_settings = config['audio_settings']
        self.recognizer = sr.Recognizer()
        
        # 调整识别器设置
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8
        
        # 语言设置
        self.languages = {
            'chinese': 'zh-CN',
            'spanish': 'es-ES',
            'auto': None  # 自动检测
        }
        
        self.current_language = 'auto'
    
    def set_language(self, language):
        """设置识别语言"""
        if language in self.languages:
            self.current_language = language
            print(f"语音识别语言设置为: {language}")
        else:
            print(f"不支持的语言: {language}")
    
    def detect_language(self, text):
        """简单的语言检测"""
        if not text:
            return 'unknown'
        
        # 检测中文字符
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len(text)
        
        if chinese_chars / total_chars > 0.3:
            return 'chinese'
        else:
            return 'spanish'
    
    def audio_data_to_audio_data(self, audio_bytes, sample_rate=16000):
        """将音频字节数据转换为AudioData对象"""
        try:
            # 创建BytesIO对象
            audio_io = BytesIO(audio_bytes)
            
            # 直接使用原始音频数据创建AudioData
            audio_data = sr.AudioData(audio_bytes, sample_rate, 2)  # 2 bytes per sample for 16-bit
            return audio_data
            
        except Exception as e:
            print(f"音频数据转换错误: {e}")
            return None
    
    def recognize_speech(self, audio_data, language=None):
        """识别语音"""
        if language is None:
            language = self.current_language
        
        results = {}
        
        try:
            # 尝试中文识别
            if language in ['chinese', 'auto']:
                try:
                    chinese_text = self.recognizer.recognize_google(
                        audio_data, 
                        language=self.languages['chinese']
                    )
                    if chinese_text:
                        results['chinese'] = chinese_text
                        results['detected_language'] = 'chinese'
                        print(f"中文识别结果: {chinese_text}")
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"中文识别请求错误: {e}")
            
            # 尝试西班牙语识别
            if language in ['spanish', 'auto']:
                try:
                    spanish_text = self.recognizer.recognize_google(
                        audio_data, 
                        language=self.languages['spanish']
                    )
                    if spanish_text:
                        results['spanish'] = spanish_text
                        if 'detected_language' not in results:
                            results['detected_language'] = 'spanish'
                        print(f"西班牙语识别结果: {spanish_text}")
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"西班牙语识别请求错误: {e}")
            
            # 如果是自动检测模式，选择最佳结果
            if language == 'auto' and results:
                if 'chinese' in results and 'spanish' in results:
                    # 选择较长的识别结果
                    chinese_len = len(results['chinese'])
                    spanish_len = len(results['spanish'])
                    
                    if chinese_len > spanish_len:
                        results['best_result'] = results['chinese']
                        results['detected_language'] = 'chinese'
                    else:
                        results['best_result'] = results['spanish']
                        results['detected_language'] = 'spanish'
                elif 'chinese' in results:
                    results['best_result'] = results['chinese']
                    results['detected_language'] = 'chinese'
                elif 'spanish' in results:
                    results['best_result'] = results['spanish']
                    results['detected_language'] = 'spanish'
            elif language == 'chinese' and 'chinese' in results:
                results['best_result'] = results['chinese']
            elif language == 'spanish' and 'spanish' in results:
                results['best_result'] = results['spanish']
            
            return results
            
        except Exception as e:
            print(f"语音识别错误: {e}")
            return {}
    
    def recognize_from_bytes(self, audio_bytes, sample_rate=16000, language=None):
        """从音频字节数据识别语音"""
        audio_data = self.audio_data_to_audio_data(audio_bytes, sample_rate)
        if audio_data:
            return self.recognize_speech(audio_data, language)
        return {}
    
    def recognize_from_file(self, filename, language=None):
        """从音频文件识别语音"""
        try:
            with sr.AudioFile(filename) as source:
                audio_data = self.recognizer.record(source)
                return self.recognize_speech(audio_data, language)
        except Exception as e:
            print(f"文件识别错误: {e}")
            return {}

class SpeechRecognitionService:
    """语音识别服务类，支持异步处理"""
    
    def __init__(self, config_file="config.json"):
        self.recognizer = SpeechRecognizer(config_file)
        self.recognition_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_thread = None
        self.is_running = False
    
    def start_service(self):
        """启动识别服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_recognition)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        print("语音识别服务已启动")
    
    def stop_service(self):
        """停止识别服务"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()
        print("语音识别服务已停止")
    
    def add_audio_for_recognition(self, audio_bytes, sample_rate=16000):
        """添加音频数据到识别队列"""
        self.recognition_queue.put((audio_bytes, sample_rate))
    
    def get_recognition_result(self):
        """获取识别结果"""
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None
    
    def _process_recognition(self):
        """处理识别队列中的音频数据"""
        while self.is_running:
            try:
                audio_bytes, sample_rate = self.recognition_queue.get(timeout=1)
                result = self.recognizer.recognize_from_bytes(audio_bytes, sample_rate)
                if result and 'best_result' in result:
                    self.result_queue.put(result)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"识别处理错误: {e}")

if __name__ == "__main__":
    # 测试语音识别
    recognizer = SpeechRecognizer()
    
    print("语音识别测试")
    print("支持的语言: chinese, spanish, auto")
    
    # 可以在这里添加测试代码