"""Environment-backed configuration for the InsureFlow voice bot."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VoiceBotSettings(BaseSettings):
    """Settings used by the Pipecat voice bot runtime and providers."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="InsureFlow Voice Bot", alias="VOICE_BOT_APP_NAME")
    log_level: str = Field(default="INFO", alias="VOICE_BOT_LOG_LEVEL")
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="VOICE_BOT_GROQ_MODEL")
    deepgram_api_key: str = Field(..., alias="DEEPGRAM_API_KEY")
    cartesia_api_key: str = Field(..., alias="CARTESIA_API_KEY")
    cartesia_voice_id: str = Field(
        default="71a7ad14-091c-4e8e-a314-022ece01c121",
        alias="VOICE_BOT_CARTESIA_VOICE_ID",
    )
    initial_prompt: str = Field(
        default="Greet the user briefly and ask what they need help with.",
        alias="VOICE_BOT_INITIAL_PROMPT",
    )
    greeting_message: str = Field(
        default="Hello, this is InsureFlow. How can I help you today?",
        alias="VOICE_BOT_GREETING_MESSAGE",
    )
    function_call_acknowledgement: str = Field(
        default="One moment while I check that for you.",
        alias="VOICE_BOT_FUNCTION_CALL_ACKNOWLEDGEMENT",
    )


@lru_cache(maxsize=1)
def get_voice_bot_settings() -> VoiceBotSettings:
    """Return a cached voice bot settings object for the current process."""

    return VoiceBotSettings()
