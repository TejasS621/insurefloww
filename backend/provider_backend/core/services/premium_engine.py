"""Premium calculation helpers for provider quote generation."""

from __future__ import annotations

from dataclasses import dataclass

from backend.provider_backend.core.apis.schemas.shared import InsuranceType
from backend.provider_backend.core.models.provider_quote_model import RiskCategory


@dataclass(slots=True)
class PremiumBreakdown:
    """Calculated premium values for a generated quote."""

    base_premium: float
    tax_amount: float
    total_premium: float


class PremiumEngine:
    """Produce deterministic premium calculations from risk and coverage data."""

    BASE_RATE_MULTIPLIERS = {
        InsuranceType.HEALTH: 0.015,
        InsuranceType.LIFE: 0.010,
        InsuranceType.VEHICLE: 0.022,
        InsuranceType.TRAVEL: 0.008,
        InsuranceType.HOME: 0.006,
    }

    RISK_MULTIPLIERS = {
        RiskCategory.LOW: 1.0,
        RiskCategory.MEDIUM: 1.18,
        RiskCategory.HIGH: 1.35,
    }

    def calculate(
        self,
        *,
        insurance_type: InsuranceType,
        coverage_amount: float,
        risk_category: RiskCategory,
        plan_multiplier: float = 1.0,
    ) -> PremiumBreakdown:
        """Calculate a premium from coverage amount and risk category."""
        base_rate = self.BASE_RATE_MULTIPLIERS.get(insurance_type, 0.01)
        risk_multiplier = self.RISK_MULTIPLIERS[risk_category]

        base_premium = round(coverage_amount * base_rate * risk_multiplier * plan_multiplier, 2)
        tax_amount = round(base_premium * 0.18, 2)
        total_premium = round(base_premium + tax_amount, 2)
        return PremiumBreakdown(
            base_premium=base_premium,
            tax_amount=tax_amount,
            total_premium=total_premium,
        )


premium_engine = PremiumEngine()

