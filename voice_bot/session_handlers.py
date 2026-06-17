"""Lifecycle hook registration for InsureFlow voice bot sessions."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from voice_bot.config import VoiceBotSettings

try:
    from pipecat.frames.frames import TTSSpeakFrame
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    raise RuntimeError(
        "Pipecat voice dependencies are not installed. Install voice_bot/requirements.txt first."
    ) from exc


def register_llm_event_handlers(
    *,
    llm: Any,
    tts: Any,
    settings: VoiceBotSettings,
) -> None:
    """Register LLM hooks that acknowledge function-call tool execution."""

    @llm.event_handler("on_function_calls_started")
    async def on_function_calls_started(service: object, function_calls: list[object]) -> None:
        """Acknowledge backend work before tool execution completes."""

        del service, function_calls
        await tts.queue_frame(TTSSpeakFrame(settings.function_call_acknowledgement))


def register_session_event_handlers(
    *,
    transport: Any,
    worker: Any,
    tts: Any,
    context: Any,
    settings: VoiceBotSettings,
    logger: logging.Logger,
) -> None:
    """Register transport and worker hooks for greeting and disconnect flow."""

    greeting_state = {"sent": False}

    async def reconcile_smallwebrtc_client() -> None:
        """Recover SmallWebRTC sessions that connected before transport setup finished."""

        client = getattr(transport, "_client", None)
        if client is None:
            return

        if not getattr(client, "is_connected", False):
            return

        if getattr(client, "_params", None) is None:
            return

        if (
            getattr(client, "_audio_input_track", None) is None
            and getattr(client, "_audio_output_track", None) is None
        ):
            logger.info("reconciling early SmallWebRTC connection after pipeline startup")
            await client._handle_client_connected()
            capture_audio = getattr(transport, "capture_participant_audio", None)
            if callable(capture_audio):
                await capture_audio()

    async def retry_smallwebrtc_attachment() -> None:
        """Retry SmallWebRTC track attachment for a short window after connect."""

        for _ in range(8):
            await asyncio.sleep(0.5)
            await reconcile_smallwebrtc_client()

    @worker.event_handler("on_pipeline_started")
    async def on_pipeline_started(worker_instance: object, frame: object) -> None:
        """Ensure SmallWebRTC tracks are attached after the pipeline is ready."""

        del worker_instance, frame
        await reconcile_smallwebrtc_client()

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport_instance: object, client: object) -> None:
        """Log the transport-level connection event for debugging."""

        del transport_instance, client
        logger.info("voice client connected")
        await reconcile_smallwebrtc_client()
        asyncio.create_task(retry_smallwebrtc_attachment())

    @worker.rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi: object) -> None:
        """Send the initial greeting only after the RTVI client is ready."""

        del rtvi
        if greeting_state["sent"]:
            return

        greeting_state["sent"] = True
        logger.info("voice client ready for audio")
        await asyncio.sleep(0.75)
        context.add_message({"role": "developer", "content": settings.initial_prompt})
        context.add_message({"role": "assistant", "content": settings.greeting_message})
        await tts.queue_frame(TTSSpeakFrame(settings.greeting_message))

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport_instance: object, client: object) -> None:
        """Cancel pipeline work when the caller disconnects."""

        del transport_instance, client
        logger.info("voice client disconnected")
        greeting_state["sent"] = False
        await worker.cancel()

