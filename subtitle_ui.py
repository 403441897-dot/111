import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
import time
from datetime import datetime
import queue

class SubtitleDisplay:
    def __init__(self, config_file="config.json"):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.ui_settings = config['ui_settings']
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("实时双语同传翻译 - 中文/西班牙语")
        self.root.geometry(f"{self.ui_settings['window_width']}x{self.ui_settings['window_height']}")
        self.root.configure(bg=self.ui_settings['bg_color'])
        
        # 设置窗口图标和属性
        self.root.resizable(True, True)
        
        # 字幕数据队列
        self.subtitle_queue = queue.Queue()
        
        # 字幕历史记录
        self.subtitle_history = []
        self.max_history = 100
        
        # 控制变量
        self.is_running = False
        self.auto_scroll = tk.BooleanVar(value=True)
        self.show_timestamp = tk.BooleanVar(value=True)
        self.font_size = tk.IntVar(value=self.ui_settings['font_size'])
        
        self.setup_ui()
        self.setup_update_thread()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建控制面板
        self.create_control_panel(main_frame)
        
        # 创建字幕显示区域
        self.create_subtitle_area(main_frame)
        
        # 创建状态栏
        self.create_status_bar(main_frame)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="5")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行控制按钮
        button_frame1 = ttk.Frame(control_frame)
        button_frame1.pack(fill=tk.X, pady=2)
        
        self.start_button = ttk.Button(
            button_frame1, 
            text="开始录音", 
            command=self.toggle_recording,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_button = ttk.Button(
            button_frame1, 
            text="清除字幕", 
            command=self.clear_subtitles
        )
        self.clear_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_button = ttk.Button(
            button_frame1, 
            text="保存记录", 
            command=self.save_history
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 第二行设置选项
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, pady=2)
        
        # 自动滚动选项
        self.auto_scroll_check = ttk.Checkbutton(
            options_frame,
            text="自动滚动",
            variable=self.auto_scroll
        )
        self.auto_scroll_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # 显示时间戳选项
        self.timestamp_check = ttk.Checkbutton(
            options_frame,
            text="显示时间戳",
            variable=self.show_timestamp
        )
        self.timestamp_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # 字体大小调节
        ttk.Label(options_frame, text="字体大小:").pack(side=tk.LEFT, padx=(0, 5))
        font_scale = ttk.Scale(
            options_frame,
            from_=10,
            to=24,
            variable=self.font_size,
            orient=tk.HORIZONTAL,
            length=100,
            command=self.update_font_size
        )
        font_scale.pack(side=tk.LEFT, padx=(0, 5))
        
        self.font_size_label = ttk.Label(options_frame, text=str(self.font_size.get()))
        self.font_size_label.pack(side=tk.LEFT)
    
    def create_subtitle_area(self, parent):
        """创建字幕显示区域"""
        # 创建双列布局
        subtitle_frame = ttk.Frame(parent)
        subtitle_frame.pack(fill=tk.BOTH, expand=True)
        
        # 中文字幕区域
        chinese_frame = ttk.LabelFrame(subtitle_frame, text="中文 (Chinese)", padding="5")
        chinese_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.chinese_text = scrolledtext.ScrolledText(
            chinese_frame,
            wrap=tk.WORD,
            font=(self.ui_settings['font_family'], self.font_size.get()),
            bg=self.ui_settings['bg_color'],
            fg=self.ui_settings['chinese_color'],
            insertbackground=self.ui_settings['chinese_color'],
            selectbackground="#333333",
            relief=tk.FLAT,
            borderwidth=1
        )
        self.chinese_text.pack(fill=tk.BOTH, expand=True)
        
        # 西班牙语字幕区域
        spanish_frame = ttk.LabelFrame(subtitle_frame, text="Español (Spanish)", padding="5")
        spanish_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.spanish_text = scrolledtext.ScrolledText(
            spanish_frame,
            wrap=tk.WORD,
            font=(self.ui_settings['font_family'], self.font_size.get()),
            bg=self.ui_settings['bg_color'],
            fg=self.ui_settings['spanish_color'],
            insertbackground=self.ui_settings['spanish_color'],
            selectbackground="#333333",
            relief=tk.FLAT,
            borderwidth=1
        )
        self.spanish_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置文本框为只读
        self.chinese_text.config(state=tk.DISABLED)
        self.spanish_text.config(state=tk.DISABLED)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(
            status_frame, 
            text="就绪 - 点击'开始录音'开始实时翻译",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 右侧显示统计信息
        self.stats_label = ttk.Label(
            status_frame,
            text="字幕条数: 0",
            relief=tk.SUNKEN,
            anchor=tk.E
        )
        self.stats_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def setup_update_thread(self):
        """设置UI更新线程"""
        self.update_thread = threading.Thread(target=self.update_ui_loop, daemon=True)
        self.update_thread.start()
    
    def update_ui_loop(self):
        """UI更新循环"""
        while True:
            try:
                # 处理字幕队列
                subtitle_data = self.subtitle_queue.get(timeout=0.1)
                self.root.after(0, self.add_subtitle_to_display, subtitle_data)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"UI更新错误: {e}")
    
    def add_subtitle(self, original_text, translated_text, source_lang, target_lang):
        """添加字幕到显示队列"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        subtitle_data = {
            'timestamp': timestamp,
            'original_text': original_text,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang
        }
        
        self.subtitle_queue.put(subtitle_data)
        
        # 添加到历史记录
        self.subtitle_history.append(subtitle_data)
        if len(self.subtitle_history) > self.max_history:
            self.subtitle_history.pop(0)
    
    def add_subtitle_to_display(self, subtitle_data):
        """在显示区域添加字幕"""
        timestamp = subtitle_data['timestamp']
        original_text = subtitle_data['original_text']
        translated_text = subtitle_data['translated_text']
        source_lang = subtitle_data['source_lang']
        target_lang = subtitle_data['target_lang']
        
        # 根据源语言决定显示位置
        if source_lang == 'chinese':
            chinese_text_widget = self.chinese_text
            spanish_text_widget = self.spanish_text
            chinese_content = original_text
            spanish_content = translated_text
        else:
            chinese_text_widget = self.chinese_text
            spanish_text_widget = self.spanish_text
            chinese_content = translated_text
            spanish_content = original_text
        
        # 格式化显示文本
        if self.show_timestamp.get():
            chinese_display = f"[{timestamp}] {chinese_content}\n\n"
            spanish_display = f"[{timestamp}] {spanish_content}\n\n"
        else:
            chinese_display = f"{chinese_content}\n\n"
            spanish_display = f"{spanish_content}\n\n"
        
        # 更新中文显示区域
        chinese_text_widget.config(state=tk.NORMAL)
        chinese_text_widget.insert(tk.END, chinese_display)
        if self.auto_scroll.get():
            chinese_text_widget.see(tk.END)
        chinese_text_widget.config(state=tk.DISABLED)
        
        # 更新西班牙语显示区域
        spanish_text_widget.config(state=tk.NORMAL)
        spanish_text_widget.insert(tk.END, spanish_display)
        if self.auto_scroll.get():
            spanish_text_widget.see(tk.END)
        spanish_text_widget.config(state=tk.DISABLED)
        
        # 更新统计信息
        self.stats_label.config(text=f"字幕条数: {len(self.subtitle_history)}")
    
    def toggle_recording(self):
        """切换录音状态"""
        if not self.is_running:
            self.is_running = True
            self.start_button.config(text="停止录音")
            self.status_label.config(text="正在录音和翻译...")
            # 这里应该启动录音和翻译服务
            if hasattr(self, 'on_start_recording'):
                self.on_start_recording()
        else:
            self.is_running = False
            self.start_button.config(text="开始录音")
            self.status_label.config(text="已停止录音")
            # 这里应该停止录音和翻译服务
            if hasattr(self, 'on_stop_recording'):
                self.on_stop_recording()
    
    def clear_subtitles(self):
        """清除所有字幕"""
        # 清除显示区域
        self.chinese_text.config(state=tk.NORMAL)
        self.chinese_text.delete(1.0, tk.END)
        self.chinese_text.config(state=tk.DISABLED)
        
        self.spanish_text.config(state=tk.NORMAL)
        self.spanish_text.delete(1.0, tk.END)
        self.spanish_text.config(state=tk.DISABLED)
        
        # 清除历史记录
        self.subtitle_history.clear()
        
        # 更新统计信息
        self.stats_label.config(text="字幕条数: 0")
        self.status_label.config(text="字幕已清除")
    
    def save_history(self):
        """保存字幕历史记录"""
        if not self.subtitle_history:
            messagebox.showwarning("警告", "没有字幕记录可保存")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="保存字幕记录"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.subtitle_history, f, ensure_ascii=False, indent=2)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        for subtitle in self.subtitle_history:
                            f.write(f"[{subtitle['timestamp']}]\n")
                            f.write(f"原文({subtitle['source_lang']}): {subtitle['original_text']}\n")
                            f.write(f"译文({subtitle['target_lang']}): {subtitle['translated_text']}\n")
                            f.write("-" * 50 + "\n\n")
                
                messagebox.showinfo("成功", f"字幕记录已保存到: {filename}")
                self.status_label.config(text=f"已保存到: {filename}")
                
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def update_font_size(self, value):
        """更新字体大小"""
        size = int(float(value))
        self.font_size_label.config(text=str(size))
        
        # 更新字体
        new_font = (self.ui_settings['font_family'], size)
        self.chinese_text.config(font=new_font)
        self.spanish_text.config(font=new_font)
    
    def set_callbacks(self, on_start=None, on_stop=None):
        """设置回调函数"""
        if on_start:
            self.on_start_recording = on_start
        if on_stop:
            self.on_stop_recording = on_stop
    
    def update_status(self, message):
        """更新状态信息"""
        self.status_label.config(text=message)
    
    def run(self):
        """运行UI主循环"""
        self.root.mainloop()
    
    def destroy(self):
        """销毁窗口"""
        self.root.destroy()

class SubtitleWindow:
    """独立的字幕窗口类，用于创建多个字幕显示窗口"""
    
    def __init__(self, title="字幕窗口", language="chinese", config_file="config.json"):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.ui_settings = config['ui_settings']
        self.language = language
        
        # 创建窗口
        self.window = tk.Toplevel()
        self.window.title(title)
        self.window.geometry("400x300")
        
        # 设置颜色
        if language == "chinese":
            text_color = self.ui_settings['chinese_color']
        else:
            text_color = self.ui_settings['spanish_color']
        
        # 创建文本显示区域
        self.text_widget = scrolledtext.ScrolledText(
            self.window,
            wrap=tk.WORD,
            font=(self.ui_settings['font_family'], self.ui_settings['font_size']),
            bg=self.ui_settings['bg_color'],
            fg=text_color,
            insertbackground=text_color,
            relief=tk.FLAT,
            borderwidth=1
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text_widget.config(state=tk.DISABLED)
    
    def add_text(self, text, timestamp=None):
        """添加文本到窗口"""
        if timestamp:
            display_text = f"[{timestamp}] {text}\n\n"
        else:
            display_text = f"{text}\n\n"
        
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, display_text)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
    
    def clear(self):
        """清除窗口内容"""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)
    
    def destroy(self):
        """销毁窗口"""
        self.window.destroy()

if __name__ == "__main__":
    # 测试字幕显示
    def test_subtitle_display():
        app = SubtitleDisplay()
        
        # 模拟添加字幕
        def add_test_subtitles():
            time.sleep(2)
            app.add_subtitle("你好，欢迎使用实时翻译系统", "Hola, bienvenido al sistema de traducción en tiempo real", "chinese", "spanish")
            time.sleep(3)
            app.add_subtitle("¿Cómo estás hoy?", "你今天怎么样？", "spanish", "chinese")
            time.sleep(3)
            app.add_subtitle("这个系统可以实时翻译中文和西班牙语", "Este sistema puede traducir chino y español en tiempo real", "chinese", "spanish")
        
        # 在后台线程中添加测试字幕
        test_thread = threading.Thread(target=add_test_subtitles, daemon=True)
        test_thread.start()
        
        app.run()
    
    test_subtitle_display()