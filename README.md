# Voice Assistant with OpenAI and IBM Watson

This project exposes a small Flask backend and static front end that work together to provide a conversational voice assistant. The browser captures audio, sends it to the backend for transcription, forwards the transcribed text to OpenAI for a response, and finally converts the response back to speech.

## Prerequisites

- Python 3.10+
- An OpenAI API key (`OPENAI_API_KEY`)
- Either locally running IBM Watson Speech services (see `models/stt` and `models/tts`) or hosted service credentials (`STT_URL`, `TTS_URL`, and respective auth headers)

## Quick Start

1. Create and activate a virtual environment, then install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Export configuration (example for local Docker containers):
   ```powershell
   $env:OPENAI_API_KEY = "<your key>"
   $env:STT_URL = "http://localhost:1080/speech-to-text/api/v1/recognize"
   $env:TTS_URL = "http://localhost:1081/text-to-speech/api/v1/synthesize"
   ```
3. Run the Flask app:
   ```powershell
   python server.py
   ```
4. Open `http://localhost:8000` and interact with the assistant.

## Environment Variables

| Variable           | Purpose                               | Default                                                  |
| ------------------ | ------------------------------------- | -------------------------------------------------------- |
| `OPENAI_API_KEY`   | Credentials for OpenAI API            | `skills-network` (lab placeholder)                       |
| `OPENAI_MODEL`     | Chat completion model name            | `gpt-3.5-turbo`                                          |
| `STT_URL`          | Speech-to-Text endpoint               | `http://localhost:1080/speech-to-text/api/v1/recognize`  |
| `TTS_URL`          | Text-to-Speech endpoint               | `http://localhost:1081/text-to-speech/api/v1/synthesize` |
| `STT_MODEL`        | Optional model query parameter        | unset                                                    |
| `TTS_ACCEPT`       | Audio mime type expected from TTS     | `audio/wav`                                              |
| `STT_CONTENT_TYPE` | Content type sent to STT              | `application/octet-stream`                               |
| `STT_AUTH_HEADER`  | Authorization header for STT requests | unset                                                    |
| `TTS_AUTH_HEADER`  | Authorization header for TTS requests | unset                                                    |

Additional options such as `OPENAI_SYSTEM_PROMPT`, `OPENAI_TEMPERATURE`, `STT_TIMEOUT`, and `TTS_TIMEOUT` are also supported.

## Error Handling

The backend surfaces errors with HTTP 4xx/5xx status codes and an `error` string in the JSON response. Review the Flask logs for detailed tracebacks when debugging service-to-service calls.

## Local Watson Services

If you prefer fully local transcription and synthesis, build and run the Docker images described under `models/stt` and `models/tts`. The defaults in this repository assume the STT container listens on port `1080` and the TTS container on `1081`.
