# InsureFlow Voice Bot

This package adds a Pipecat-based voice assistant for InsureFlow customer workflows. It uses:

- Pipecat for the real-time voice pipeline
- Deepgram for speech-to-text
- OpenAI for reasoning and tool selection
- Cartesia for text-to-speech
- Existing `insureflow_mcp` tools as the orchestration layer

The voice bot does not implement underwriting, quote pricing, payment processing, policy issuance, or ticket business logic. It validates voice inputs, calls the existing InsureFlow API tool layer, and speaks back the result.

## Supported Voice Workflows

- Request customer OTP
- Verify customer OTP
- Generate quote
- Select quote
- Initiate payment
- Check payment status
- Get policy details
- Create support ticket

## Folder Overview

- `voice_bot/config.py`
  Reads environment variables for Pipecat and provider keys.
- `voice_bot/runtime.py`
  Builds the shared MCP-backed tool runtime and in-memory auth session.
- `voice_bot/functions.py`
  Registers Pipecat function-calling tools that map 1-to-1 to existing `insureflow_mcp` tools.
- `voice_bot/prompts.py`
  Holds the system instruction used by the voice assistant.
- `voice_bot/bot.py`
  Builds the Pipecat audio pipeline and transport hooks.
- `voice_bot/__main__.py`
  Allows `python -m voice_bot` to start the bot.

## Environment Variables

Copy `voice_bot/.env.example` into your repo-level `.env` or merge those values into your existing `.env`.

Required voice provider variables:

- `GROQ_API_KEY`
- `DEEPGRAM_API_KEY`
- `CARTESIA_API_KEY`

Common backend variables already reused from the MCP layer:

- `MAIN_BACKEND_URL`
- `MCP_REQUEST_TIMEOUT_SECONDS`
- `MCP_MAX_RETRIES`
- `MCP_RETRY_BACKOFF_SECONDS`

Optional voice bot tuning variables:

- `VOICE_BOT_GROQ_MODEL`
- `VOICE_BOT_CARTESIA_VOICE_ID`
- `VOICE_BOT_INITIAL_PROMPT`
- `VOICE_BOT_GREETING_MESSAGE`
- `VOICE_BOT_FUNCTION_CALL_ACKNOWLEDGEMENT`

## Install

```powershell
pip install -r voice_bot/requirements.txt
```

If you already use the repo virtual environment, run that command from the repository root.

## Local Run

Use the provided PowerShell helper from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-voice-bot.ps1
```

You can also pass Pipecat runner arguments through the script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-voice-bot.ps1 --transport twilio
```

## Runtime Flow

1. Pipecat receives audio from the selected transport.
2. Deepgram converts speech into text.
3. OpenAI decides whether it can answer directly or should call a tool.
4. Tool calls are routed into the existing `insureflow_mcp` tool classes.
5. Those tools call the real InsureFlow backend APIs.
6. The result is returned to OpenAI.
7. Cartesia speaks the final natural-language response back to the caller.

## Notes

- Customer authentication is session-based in memory. Once OTP verification succeeds, later authenticated tools in the same bot process can reuse that token.
- This package intentionally avoids direct backend business logic. If a workflow changes, update the main backend or `insureflow_mcp` layer first.
