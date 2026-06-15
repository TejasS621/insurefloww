"""Request and response schemas shared by broker-related integrations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BrokerSummaryOutput(BaseModel):
    """Broker summary returned to shared clients."""

    model_config = ConfigDict(extra="forbid")

    broker_code: str
    broker_name: str
    status: str
    callback_url: str
    webhook_url: str


class RegisterBrokerInput(BaseModel):
    """Input accepted by broker-registration helpers."""

    model_config = ConfigDict(extra="forbid")

    broker_name: str = Field(..., min_length=2, max_length=120)
    broker_code: str = Field(..., min_length=2, max_length=50)
    callback_url: HttpUrl
    webhook_url: HttpUrl


class RegisterBrokerOutput(BaseModel):
    """Broker registration result returned to shared clients."""

    model_config = ConfigDict(extra="forbid")

    broker_code: str
    api_key: str | None = None
    created_at: str | None = None
    status: str
