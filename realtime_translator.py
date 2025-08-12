#!/usr/bin/env python3
"""
Real-time Chinese ↔ Mexican Spanish (Latin American Spanish) simultaneous translation using:
- Microphone audio input
- OpenAI Whisper speech-to-text API for transcription
- ChatGPT (GPT-4-o by default) for translation
- Tkinter GUI with dual scrolling subtitle panes (Chinese & Spanish)

Prerequisites:
1. Install dependencies from requirements.txt
2. Export OpenAI API key as OPENAI_API_KEY environment variable or place it in a .env file

Usage:
$ python realtime_translator.py
"""
import os
import threading
import queue
import tempfile
import time
from dataclasses import dataclass
from typing import Tuple

import sounddevice as sd
import soundfile as sf
import openai
from dotenv import load_dotenv
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

CHUNK_SECONDS = 5           # length of each recorded chunk in seconds
SAMPLE_RATE = 16000         # Whisper works best with 16 kHz audio
CHANNELS = 1                # mono audio is sufficient
TRANSLATE_MODEL = "gpt-4o-mini"  # Change to "gpt-4o" if you have access
WHISPER_MODEL = "whisper-1"      # OpenAI hosted Whisper model name

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise EnvironmentError("OPENAI_API_KEY not set. Export it or add to .env file.")

# -----------------------------------------------------------------------------
# Utility dataclasses
# -----------------------------------------------------------------------------

@dataclass
class Transcript:
    text: str
    language: str  # ISO 639-1 language code (e.g., "zh", "es")

# -----------------------------------------------------------------------------
# Audio recording → Transcription
# -----------------------------------------------------------------------------

def record_chunk(seconds: int = CHUNK_SECONDS, samplerate: int = SAMPLE_RATE) -> Tuple[str, str]:
    """Record microphone audio for `seconds` and save to a temporary .wav file.

    Returns (filepath, mimetype)
    """
    frames = int(seconds * samplerate)
    print("[Recorder] Recording chunk …")
    audio = sd.rec(frames, samplerate=samplerate, channels=CHANNELS, dtype="float32")
    sd.wait()
    tmpfile = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmpfile.name, audio, samplerate)
    print(f"[Recorder] Saved chunk to {tmpfile.name}")
    return tmpfile.name, "audio/wav"


def transcribe(audio_path: str) -> Transcript:
    """Call OpenAI Whisper API to transcribe audio file."""
    print("[Whisper] Transcribing …")
    with open(audio_path, "rb") as f:
        response = openai.Audio.transcribe(
            model=WHISPER_MODEL,
            file=f,
            response_format="json",
            temperature=0.0,
        )
    text = response["text"].strip()
    language = response.get("language", "")
    print(f"[Whisper] Detected {language}: {text}")
    return Transcript(text=text, language=language)

# -----------------------------------------------------------------------------
# Translation via ChatGPT
# -----------------------------------------------------------------------------

def translate_with_chatgpt(text: str, src_lang: str) -> str:
    """Translate text between Chinese and Spanish using ChatGPT."""
    if src_lang.startswith("zh"):
        prompt = (
            "你是专业的双语同声传译，现在请将以下文本从中文翻译成墨西哥西班牙语（拉丁美洲西班牙语），保持口语化并且准确：\n" + text
        )
    else:
        prompt = (
            "Eres un intérprete profesional. Traduce el siguiente texto del español latinoamericano al chino mandarín coloquial con precisión:\n" + text
        )
    print("[GPT] Requesting translation …")
    completion = openai.ChatCompletion.create(
        model=TRANSLATE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        timeout=60,
    )
    translation = completion.choices[0].message["content"].strip()
    print(f"[GPT] Translation: {translation}")
    return translation

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

class SubtitleGUI:
    """Simple Tkinter GUI with two scrolling text panes."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("中西实时同传字幕 | Chinese ↔ Spanish Interpreter")
        self.root.geometry("1200x400")

        # Chinese pane (top)
        self.ch_text = ScrolledText(self.root, font=("Helvetica", 14), wrap=tk.WORD, height=10)
        self.ch_text.pack(fill=tk.BOTH, expand=True)
        self.ch_text.insert(tk.END, "--- 中文字幕 ---\n")
        self.ch_text.configure(state=tk.DISABLED)

        # Spanish pane (bottom)
        self.es_text = ScrolledText(self.root, font=("Helvetica", 14), wrap=tk.WORD, height=10)
        self.es_text.pack(fill=tk.BOTH, expand=True)
        self.es_text.insert(tk.END, "--- Subtítulos en español ---\n")
        self.es_text.configure(state=tk.DISABLED)

    def append(self, zh: str = "", es: str = ""):
        """Append subtitles to GUI panes safely from any thread."""
        def _append():
            if zh:
                self.ch_text.configure(state=tk.NORMAL)
                self.ch_text.insert(tk.END, zh + "\n")
                self.ch_text.see(tk.END)
                self.ch_text.configure(state=tk.DISABLED)
            if es:
                self.es_text.configure(state=tk.NORMAL)
                self.es_text.insert(tk.END, es + "\n")
                self.es_text.see(tk.END)
                self.es_text.configure(state=tk.DISABLED)
        # Schedule update in main thread
        self.root.after(0, _append)

    def run(self):
        self.root.mainloop()

# -----------------------------------------------------------------------------
# Processing thread
# -----------------------------------------------------------------------------

def processing_loop(gui: SubtitleGUI, stop_event: threading.Event):
    """Continuously record, transcribe, translate, and update GUI until stop_event set."""
    while not stop_event.is_set():
        try:
            audio_path, _ = record_chunk()
            transcript = transcribe(audio_path)
            if not transcript.text:
                continue  # skip empty
            translation = translate_with_chatgpt(transcript.text, transcript.language)

            if transcript.language.startswith("zh"):
                zh = transcript.text
                es = translation
            else:
                es = transcript.text
                zh = translation

            gui.append(zh=zh, es=es)
        except Exception as e:
            print("[Error]", e)
            time.sleep(1)

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main():
    gui = SubtitleGUI()
    stop_event = threading.Event()
    t = threading.Thread(target=processing_loop, args=(gui, stop_event), daemon=True)
    t.start()

    try:
        gui.run()
    finally:
        stop_event.set()
        t.join()


if __name__ == "__main__":
    main()