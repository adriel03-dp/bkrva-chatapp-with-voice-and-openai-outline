import logging
import os
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from worker import (
    encode_audio_to_base64,
    openai_process_message,
    speech_to_text,
    text_to_speech,
)

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/speech-to-text', methods=['POST'])
def speech_to_text_route():
    audio_bytes = request.get_data()
    content_type = request.headers.get('Content-Type')

    if not audio_bytes:
        return jsonify({'error': 'No audio payload provided'}), 400

    try:
        transcript = speech_to_text(audio_bytes, content_type)
    except Exception as exc:  # noqa: BLE001 - return message to client
        logger.exception('Speech-to-text conversion failed')
        return jsonify({'error': 'Speech-to-text conversion failed', 'details': str(exc)}), 502

    return jsonify({'text': transcript})


@app.route('/process-message', methods=['POST'])
def process_prompt_route():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    user_message = (payload.get('userMessage') or '').strip()
    voice = (payload.get('voice') or '').strip()

    if not user_message:
        return jsonify({'error': 'userMessage is required'}), 400

    try:
        assistant_text = openai_process_message(user_message)
    except Exception as exc:  # noqa: BLE001 - expose reason to assist debugging
        logger.exception('OpenAI processing failed')
        return jsonify({'error': 'Unable to process user message', 'details': str(exc)}), 502

    audio_b64 = ""
    try:
        audio_bytes = text_to_speech(assistant_text, voice)
        audio_b64 = encode_audio_to_base64(audio_bytes)
    except Exception as exc:  # noqa: BLE001 - log but allow graceful fallback
        logger.exception('Text-to-speech synthesis failed')

    response = {
        'openaiResponseText': assistant_text,
        'openaiResponseSpeech': audio_b64,
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(port=8000, host='0.0.0.0')
