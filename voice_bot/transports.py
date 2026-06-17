"""Transport parameter builders for supported InsureFlow voice bot runtimes."""

from __future__ import annotations

from typing import Any

try:
    from pipecat.transports.base_transport import TransportParams
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    raise RuntimeError(
        "Pipecat voice dependencies are not installed. Install voice_bot/requirements.txt first."
    ) from exc


def daily_transport_params() -> Any:
    """Load Daily transport parameters only when the Daily transport is selected."""

    from pipecat.transports.daily.transport import DailyParams

    return DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    )


def twilio_transport_params() -> Any:
    """Load WebSocket transport parameters only when the Twilio transport is selected."""

    from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams

    return FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    )


def webrtc_transport_params() -> TransportParams:
    """Build transport parameters for the local WebRTC transport."""

    return TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    )


TRANSPORT_PARAMS = {
    "daily": daily_transport_params,
    "twilio": twilio_transport_params,
    "webrtc": webrtc_transport_params,
}

