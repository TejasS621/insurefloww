"""Risk assessment helpers for provider quote generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from backend.provider_backend.commons.logger import get_logger
from backend.provider_backend.core.apis.schemas.shared import HealthDetailsSchema
from backend.provider_backend.core.models.provider_quote_model import RiskCategory

logger = get_logger(__name__)


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
        date_of_birth: date | datetime,
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
            other_conditions = [
                item.strip()
                for item in health_details.other_conditions
                if isinstance(item, str) and item.strip()
            ]
            score += len(other_conditions) * 3

        if score < 25:
            category = RiskCategory.LOW
        elif score < 50:
            category = RiskCategory.MEDIUM
        else:
            category = RiskCategory.HIGH

        logger.info("Calculated provider risk score %.2f with category '%s'.", score, category.value)
        return RiskAssessment(risk_score=round(score, 2), risk_category=category)


risk_engine = RiskEngine()

