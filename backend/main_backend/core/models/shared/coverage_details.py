"""Embedded coverage selection models for main-backend records."""

from __future__ import annotations

from enum import Enum

from odmantic import EmbeddedModel, Field


class InsuranceType(str, Enum):
    HEALTH = "HEALTH"
    LIFE = "LIFE"
    VEHICLE = "VEHICLE"
    TRAVEL = "TRAVEL"
    HOME = "HOME"


class Relation(str, Enum):
    SELF = "SELF"
    SPOUSE = "SPOUSE"
    CHILD = "CHILD"
    PARENT = "PARENT"
    FAMILY = "FAMILY"


class CoverageDetails(EmbeddedModel):
    insurance_type: InsuranceType = Field(...)
    coverage_amount: float = Field(..., gt=0)
    sum_insured: float | None = Field(default=None, gt=0)
    tenure_years: int | None = Field(default=None, ge=1)
    relation: Relation | None = Field(default=None)
    insured_members: int | None = Field(default=None, ge=1)
    pan_india_cover: bool = Field(default=True)

