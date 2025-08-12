# Real-Time Chinese ↔ Mexican Spanish Interpreter

This project is a lightweight **simultaneous interpretation** tool that listens to your microphone, converts speech to text with **OpenAI Whisper**, translates it with **ChatGPT (GPT-4-o)**, and displays scrolling subtitles in two languages (Chinese & Spanish) in real-time.

> ⚠️  The program relies on OpenAI paid APIs and may accrue usage costs.

---

## Features

* Two-way: Chinese → Spanish, Spanish → Chinese
* Uses OpenAI Whisper for accurate speech recognition
* Uses GPT-4-o (or `gpt-4o-mini`) for high-quality translation
* Dual-pane GUI (Tkinter) showing live subtitles for each language
* Simple, self-contained Python script (≈200 LOC)

---

## Installation

```bash
# 1. Clone your repo / download the files, then inside the project root:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### System dependencies

* Python 3.8+
* PortAudio & TK dev libraries (for many Linux distros):
  ```bash
  sudo apt-get install portaudio19-dev python3-tk
  ```

---

## API Key

Export your OpenAI key **before** running:

```bash
export OPENAI_API_KEY="sk-…"
```

Or create a `.env` file (loaded automatically):

```env
OPENAI_API_KEY=sk-…
```

---

## Run

```bash
python realtime_translator.py
```

Speak in either Chinese or Mexican Spanish; after a short delay (≈5 s chunk size) you will see:

* The **original** text in its language
* Its **translation** in the other pane

---

## Adjustments

* `CHUNK_SECONDS` – recording chunk length; shorter = less latency, higher API cost.
* `TRANSLATE_MODEL` – switch to `gpt-4o` if you have access, or downgrade to `gpt-3.5-turbo` to save cost.
* `WHISPER_MODEL` – currently only `whisper-1` is available.

---

## Caveats

* Latency depends on chunk size and network round-trip to OpenAI.
* Whisper API currently does not support true streaming; this script simulates near-real-time by sending short chunks.
* Ensure quiet environment and use a decent microphone for best results.

---

## License

MIT