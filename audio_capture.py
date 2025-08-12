import pyaudio
import wave
import threading
import queue
import time
import json
from io import BytesIO

class AudioCapture:
    def __init__(self, config_file="config.json"):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.audio_settings = config['audio_settings']
        self.sample_rate = self.audio_settings['sample_rate']
        self.chunk_size = self.audio_settings['chunk_size']
        self.channels = self.audio_settings['channels']
        self.silence_threshold = self.audio_settings['silence_threshold']
        self.min_audio_length = self.audio_settings['min_audio_length']
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return
            
        self.is_recording = True
        
        # 创建音频流
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        # 开始录音线程
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        print("开始录音...")
    
    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        if self.recording_thread:
            self.recording_thread.join()
            
        print("停止录音")
    
    def _record_audio(self):
        """录音线程函数"""
        audio_buffer = []
        silence_count = 0
        max_silence = int(self.sample_rate / self.chunk_size * 2)  # 2秒静音
        
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_buffer.append(data)
                
                # 检测音量
                audio_data = int.from_bytes(data, byteorder='little', signed=True)
                volume = abs(audio_data)
                
                if volume < self.silence_threshold:
                    silence_count += 1
                else:
                    silence_count = 0
                
                # 如果检测到足够的静音或缓冲区足够大，处理音频
                if (silence_count >= max_silence and len(audio_buffer) > 0) or len(audio_buffer) >= 50:
                    if len(audio_buffer) >= int(self.sample_rate / self.chunk_size * self.min_audio_length):
                        audio_bytes = b''.join(audio_buffer)
                        self.audio_queue.put(audio_bytes)
                    
                    audio_buffer = []
                    silence_count = 0
                    
            except Exception as e:
                print(f"录音错误: {e}")
                break
    
    def get_audio_data(self):
        """获取音频数据"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def save_audio_to_wav(self, audio_data, filename):
        """将音频数据保存为WAV文件"""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
    
    def audio_to_wav_bytes(self, audio_data):
        """将音频数据转换为WAV格式的字节流"""
        wav_buffer = BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
        
        wav_buffer.seek(0)
        return wav_buffer.getvalue()
    
    def cleanup(self):
        """清理资源"""
        self.stop_recording()
        self.audio.terminate()

if __name__ == "__main__":
    # 测试音频捕获
    capture = AudioCapture()
    
    try:
        capture.start_recording()
        
        print("正在录音，按 Ctrl+C 停止...")
        while True:
            audio_data = capture.get_audio_data()
            if audio_data:
                print(f"捕获到音频数据: {len(audio_data)} 字节")
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n停止录音...")
    finally:
        capture.cleanup()