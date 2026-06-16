"""Embedded health-detail models for provider-side underwriting records."""

from __future__ import annotations

from odmantic import EmbeddedModel, Field


class HealthDetails(EmbeddedModel):
    height_cm: float | None = Field(default=None, ge=0)
    weight_kg: float | None = Field(default=None, ge=0)
    calculated_bmi: float | None = Field(default=None, ge=0)
    smoker: bool = Field(default=False)
    diabetes: bool = Field(default=False)
    blood_pressure: bool = Field(default=False)
    heart_ailments: bool = Field(default=False)
    pre_existing_disease: bool = Field(default=False)
    other_conditions: str | None = Field(default=None)

