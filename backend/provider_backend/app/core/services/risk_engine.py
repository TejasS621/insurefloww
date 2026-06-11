"""Risk assessment helpers for provider quote generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.provider_backend.app.core.apis.schemas.shared import HealthDetailsSchema
from backend.provider_backend.app.core.models.provider_quote_model import RiskCategory


@dataclass(slots=True)
class RiskAssessment:
    """Structured underwriting risk output."""

    risk_score: float
    risk_category: RiskCategory


class RiskEngine:
    """Provide deterministic underwriting risk scoring for quote generation."""

    def assess(
        self,
        *,
        date_of_birth: date,
        health_details: HealthDetailsSchema | None,
    ) -> RiskAssessment:
        """Calculate a coarse risk score from age and declared health factors."""
        today = date.today()
        age = today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
        score = max(age / 2, 1.0)

        if health_details is not None:
            if health_details.smoker:
                score += 20
            if health_details.diabetes:
                score += 12
            if health_details.blood_pressure:
                score += 8
            if health_details.heart_ailments:
                score += 20
            if health_details.pre_existing_disease:
                score += 15
            score += len(health_details.other_conditions) * 3

        if score < 25:
            category = RiskCategory.LOW
        elif score < 50:
            category = RiskCategory.MEDIUM
        else:
            category = RiskCategory.HIGH

        return RiskAssessment(risk_score=round(score, 2), risk_category=category)


risk_engine = RiskEngine()

