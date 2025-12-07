"""Utility helpers for STT, LLM, and TTS interactions."""

from __future__ import annotations

import base64
import logging
import os
from typing import Optional

import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

openai_client = OpenAI()

DEFAULT_STT_URL = os.getenv(
    "STT_URL", "http://localhost:1080/speech-to-text/api/v1/recognize"
)
DEFAULT_TTS_URL = os.getenv(
    "TTS_URL", "http://localhost:1081/text-to-speech/api/v1/synthesize"
)
DEFAULT_TTS_ACCEPT = os.getenv("TTS_ACCEPT", "audio/wav")
DEFAULT_STT_CONTENT_TYPE = os.getenv(
    "STT_CONTENT_TYPE", "application/octet-stream"
)
STT_AUTH_HEADER = os.getenv("STT_AUTH_HEADER")
TTS_AUTH_HEADER = os.getenv("TTS_AUTH_HEADER")


def _log_http_error(prefix: str, error: Exception) -> None:
    """Emit a concise log entry for downstream HTTP failures."""

    logger.error("%s failed: %s", prefix, error)


def speech_to_text(audio_binary: bytes, content_type: Optional[str] = None) -> str:
    """Send raw audio to the configured STT endpoint and return the transcript."""

    if not audio_binary:
        raise ValueError("No audio supplied for speech-to-text conversion")

    headers = {"Content-Type": content_type or DEFAULT_STT_CONTENT_TYPE}
    if STT_AUTH_HEADER:
        headers["Authorization"] = STT_AUTH_HEADER
    params = {}
    stt_model = os.getenv("STT_MODEL")
    if stt_model:
        params["model"] = stt_model

    try:
        response = requests.post(
            DEFAULT_STT_URL,
            headers=headers,
            params=params,
            data=audio_binary,
            timeout=float(os.getenv("STT_TIMEOUT", "30")),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        _log_http_error("Speech-to-text request", exc)
        raise

    payload = response.json()

    # Watson STT returns transcripts inside results -> alternatives
    transcripts = []
    results = payload.get("results", [])
    for result in results:
        for alternative in result.get("alternatives", []):
            transcript = alternative.get("transcript", "").strip()
            if transcript:
                transcripts.append(transcript)

    if transcripts:
        return " ".join(transcripts)

    # Some services respond with a direct "text" field
    if text := payload.get("text"):
        return text.strip()

    raise RuntimeError("Speech-to-text response did not contain a transcript")


def text_to_speech(text: str, voice: str = "") -> bytes:
    """Convert text to speech using the configured TTS endpoint."""

    if not text:
        raise ValueError("No text supplied for text-to-speech conversion")

    params = {"voice": voice} if voice else None
    headers = {"Accept": DEFAULT_TTS_ACCEPT, "Content-Type": "application/json"}
    if TTS_AUTH_HEADER:
        headers["Authorization"] = TTS_AUTH_HEADER
    body = {"text": text}

    try:
        response = requests.post(
            DEFAULT_TTS_URL,
            params=params,
            headers=headers,
            json=body,
            timeout=float(os.getenv("TTS_TIMEOUT", "30")),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        _log_http_error("Text-to-speech request", exc)
        raise

    if not response.content:
        raise RuntimeError("Text-to-speech response did not include audio data")

    return response.content


def openai_process_message(user_message: str) -> str:
    """Generate an assistant response using the configured OpenAI chat model."""

    message = (user_message or "").strip()
    if not message:
        raise ValueError("Empty user message provided to OpenAI")

    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    system_prompt = os.getenv(
        "OPENAI_SYSTEM_PROMPT",
        "You are a helpful AI voice assistant that responds clearly and concisely.",
    )
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    try:
        completion = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=temperature,
        )
    except Exception as exc:  # noqa: BLE001 - surface exact OpenAI exception
        logger.exception("OpenAI chat completion failed")
        raise

    choice = completion.choices[0]
    content = choice.message.content if choice.message else ""
    if not content:
        raise RuntimeError("OpenAI response did not include assistant content")

    return content.strip()


def encode_audio_to_base64(audio_bytes: bytes) -> str:
    """Utility to return base64 encoded audio for frontend playback."""

    if not audio_bytes:
        raise ValueError("No audio bytes provided for encoding")

    return base64.b64encode(audio_bytes).decode("ascii")
