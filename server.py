import os
import json
import tempfile
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # Will raise at runtime if not installed


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MISSING_API_KEY = not bool(OPENAI_API_KEY)

# Models: prefer modern fast STT + best translation model
STT_MODEL_CANDIDATES = [
    "gpt-4o-mini-transcribe",  # fast and accurate
    "whisper-1"  # fallback
]
TRANSLATION_MODEL = os.getenv("TRANSLATION_MODEL", "gpt-4o")

app = Flask(__name__, static_folder="static", static_url_path="/static")
ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "threading")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=ASYNC_MODE)
client = OpenAI(api_key=OPENAI_API_KEY) if not MISSING_API_KEY else None


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/upload", methods=["POST"])  # receives audio blob chunks
def upload_audio_chunk():
    # Expect raw binary audio (e.g., webm/opus) in the request body
    if not request.data:
        return {"ok": False, "error": "No audio data"}, 400

    # Save to a temporary file to pass to OpenAI STT
    suffix = ".webm"  # MediaRecorder default when using audio/webm; codecs=opus
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_path = tmp_file.name
        tmp_file.write(request.data)

    try:
        if MISSING_API_KEY:
            return {"ok": False, "error": "Server missing OPENAI_API_KEY"}, 500

        transcript_text = transcribe_file(tmp_path)
        if not transcript_text:
            return {"ok": True, "skipped": True}, 200

        # Translate using GPT-4o, returning both zh and es strings
        translation = translate_zh_es(transcript_text)

        # Massage payload for dual subtitles: always fill both columns
        zh_text = translation.get("zh", "").strip()
        es_text = translation.get("es", "").strip()
        source_lang = translation.get("source_lang", "unknown")

        # Emit to all connected clients
        socketio.emit(
            "subtitle",
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source_lang": source_lang,
                "zh": zh_text,
                "es": es_text,
                "raw": transcript_text,
            },
            broadcast=True,
        )

        return {"ok": True}, 200

    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def transcribe_file(filepath: str) -> str:
    """Try STT models in order until success. Returns transcript text or empty string."""
    last_err: Exception | None = None
    for model_name in STT_MODEL_CANDIDATES:
        try:
            with open(filepath, "rb") as f:
                resp = client.audio.transcriptions.create(
                    model=model_name,
                    file=f,
                )
            text = getattr(resp, "text", "") or (resp.get("text") if isinstance(resp, dict) else "")
            return text.strip()
        except Exception as e:
            last_err = e
            continue
    # If all models failed, raise last error
    if last_err:
        raise last_err
    return ""


def translate_zh_es(utterance: str) -> Dict[str, Any]:
    """Use GPT to detect language (Simplified Chinese or Mexican Spanish) and produce both sides.

    Returns dict: {"source_lang": "zh"|"es", "zh": str, "is_original_zh": bool, "es": str, "is_original_es": bool}
    """
    system_msg = (
        "You are a professional simultaneous interpreter for Simplified Chinese and Mexican Spanish. "
        "Given an input utterance, detect if it is Simplified Chinese (zh) or Mexican Spanish (es). "
        "If zh, translate to Mexican Spanish (es-MX) with natural, idiomatic, polite tone and faithful meaning. "
        "If es, translate to Simplified Chinese with natural, idiomatic, polite tone and faithful meaning. "
        "Return strict JSON with keys: source_lang (\"zh\" or \"es\"), zh, es. Do not include any additional commentary."
    )

    user_content = (
        "Utterance:\n" + utterance.strip() + "\n\n"
        "Rules:\n"
        "- Preserve proper names and numbers.\n"
        "- Keep punctuation and sentence boundaries natural.\n"
        "- Use Mexican Spanish vocabulary when applicable.\n"
        "- Use Simplified Chinese for zh.\n"
    )

    completion = client.chat.completions.create(
        model=TRANSLATION_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content},
        ],
    )

    content = completion.choices[0].message.content
    try:
        data = json.loads(content)
        source_lang = data.get("source_lang", "unknown")
        zh_text = data.get("zh", "").strip()
        es_text = data.get("es", "").strip()
        return {
            "source_lang": source_lang,
            "zh": zh_text,
            "es": es_text,
        }
    except Exception:
        # Fallback: if JSON parsing failed, attempt a simple heuristic
        return {
            "source_lang": "unknown",
            "zh": utterance if looks_like_chinese(utterance) else "",
            "es": utterance if not looks_like_chinese(utterance) else "",
        }


def looks_like_chinese(text: str) -> bool:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # eventlet is recommended for Flask-SocketIO to support WebSocket
    socketio.run(app, host="0.0.0.0", port=port)