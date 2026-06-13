from __future__ import annotations

from datetime import datetime
from enum import Enum

from odmantic import EmbeddedModel, Field


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class PersonalDetails(EmbeddedModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=5)
    mobile_number: str = Field(..., min_length=10, max_length=15)
    date_of_birth: datetime = Field(...)
    gender: Gender = Field(...)
    address_line_1: str = Field(..., min_length=3)
    address_line_2: str | None = Field(default=None)
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    pincode: str = Field(..., min_length=4, max_length=10)
    gstin: str | None = Field(default=None)
    politically_exposed_person: bool = Field(default=False)

