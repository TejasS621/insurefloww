"""Authentication service helpers for the main backend."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from odmantic import AIOEngine

from backend.main_backend.app.core.models.user_model import OTPPurpose, OTPToken
from backend.main_backend.app.commons.config import settings

from .service_exceptions import AuthenticationServiceError, NotFoundServiceError


@dataclass(slots=True)
class OTPDispatchResult:
    """Represents a generated OTP ready for out-of-band delivery."""

    mobile_number: str
    otp_code: str
    expires_at: datetime
    purpose: OTPPurpose


class AuthService:
    """Encapsulate OTP-centric authentication helper workflows."""

    OTP_EXPIRY_MINUTES = 10

    async def authenticate_admin_credentials(self, *, email: str, password: str) -> str:
        """Validate the configured admin credentials and return the admin identity.

        The admin login is environment-backed for now so JWT protection can be
        enabled without introducing a new persistence model in this branch.
        """
        if email.strip().lower() != settings.admin_email.strip().lower():
            raise AuthenticationServiceError("The supplied admin credentials are invalid.")
        if password != settings.admin_password:
            raise AuthenticationServiceError("The supplied admin credentials are invalid.")
        return settings.admin_email

    async def verify_admin_otp(self, *, email: str, otp_code: str) -> str:
        """Validate the configured admin OTP challenge and return the admin identity.

        This keeps the existing compatibility endpoint usable while shifting the
        actual authenticated session representation to a signed JWT access token.
        """
        if email.strip().lower() != settings.admin_email.strip().lower():
            raise AuthenticationServiceError("The supplied admin verification details are invalid.")
        if otp_code != settings.admin_otp_code:
            raise AuthenticationServiceError("The supplied admin verification details are invalid.")
        return settings.admin_email

    async def request_customer_otp(
        self,
        engine: AIOEngine,
        mobile_number: str,
        *,
        purpose: OTPPurpose = OTPPurpose.LOGIN,
    ) -> OTPDispatchResult:
        """Create and persist a one-time-password for customer login."""
        normalized_mobile = self._normalize_mobile_number(mobile_number)
        otp_code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES)

        token = OTPToken(
            mobile_number=normalized_mobile,
            otp_code_hash=self._hash_otp(otp_code),
            purpose=purpose,
            is_used=False,
            expires_at=expires_at,
        )
        await engine.save(token)

        if settings.debug:
            print(
                "[DEV OTP] "
                f"mobile_number={normalized_mobile} "
                f"purpose={purpose.value} "
                f"otp_code={otp_code} "
                f"expires_at={expires_at.isoformat()}"
            )

        return OTPDispatchResult(
            mobile_number=normalized_mobile,
            otp_code=otp_code,
            expires_at=expires_at,
            purpose=purpose,
        )

    async def verify_customer_otp(
        self,
        engine: AIOEngine,
        mobile_number: str,
        otp_code: str,
        *,
        purpose: OTPPurpose = OTPPurpose.LOGIN,
    ) -> OTPToken:
        """Validate a customer OTP and mark the matching token as used."""
        normalized_mobile = self._normalize_mobile_number(mobile_number)
        tokens = await engine.find(
            OTPToken,
            (OTPToken.mobile_number == normalized_mobile) & (OTPToken.purpose == purpose),
        )
        if not tokens:
            raise NotFoundServiceError("No OTP session exists for the provided mobile number.")

        latest_token = max(tokens, key=lambda token: self._ensure_utc(token.created_at))
        now = self._ensure_utc(datetime.now(timezone.utc))
        expires_at = self._ensure_utc(latest_token.expires_at)

        if latest_token.is_used:
            raise AuthenticationServiceError("The OTP has already been used.")
        if expires_at < now:
            raise AuthenticationServiceError("The OTP has expired. Request a new one.")
        if latest_token.otp_code_hash != self._hash_otp(otp_code):
            raise AuthenticationServiceError("The OTP provided is invalid.")

        latest_token.is_used = True
        await engine.save(latest_token)
        return latest_token

    @staticmethod
    def _normalize_mobile_number(mobile_number: str) -> str:
        """Normalize mobile input into a digits-only local format."""
        normalized = "".join(character for character in mobile_number if character.isdigit())
        if len(normalized) < 10:
            raise AuthenticationServiceError("A valid mobile number is required.")
        return normalized

    @staticmethod
    def _hash_otp(otp_code: str) -> str:
        """Hash an OTP value prior to persistence."""
        return hashlib.sha256(otp_code.encode("utf-8")).hexdigest()

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        """Normalize datetime values so naive database timestamps are treated as UTC."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


auth_service = AuthService()

