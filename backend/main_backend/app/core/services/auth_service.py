"""Authentication service helpers for the main backend."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from odmantic import AIOEngine

from backend.main_backend.app.core.models.user_model import AdminOTPToken, OTPPurpose, OTPToken
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

    async def request_admin_otp(
        self,
        engine: AIOEngine,
        *,
        email: str,
    ) -> OTPDispatchResult:
        """Create and persist a one-time-password for the admin sign-in flow."""
        if email.strip().lower() != settings.admin_email.strip().lower():
            raise AuthenticationServiceError("The supplied admin verification details are invalid.")

        upper_bound = 10 ** settings.customer_otp_length
        otp_code = f"{secrets.randbelow(upper_bound):0{settings.customer_otp_length}d}"
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.customer_otp_expiry_minutes
        )

        token = AdminOTPToken(
            email=settings.admin_email,
            otp_code_hash=self._hash_otp(otp_code),
            is_used=False,
            expires_at=expires_at,
        )
        await engine.save(token)

        return OTPDispatchResult(
            mobile_number=settings.admin_email,
            otp_code=otp_code,
            expires_at=expires_at,
            purpose=OTPPurpose.ADMIN_2FA,
        )

    async def verify_admin_otp(
        self,
        engine: AIOEngine,
        *,
        email: str,
        otp_code: str,
    ) -> str:
        """Validate the latest admin OTP challenge and return the admin identity."""
        normalized_email = email.strip().lower()
        if normalized_email != settings.admin_email.strip().lower():
            raise AuthenticationServiceError("The supplied admin verification details are invalid.")

        tokens = await engine.find(
            AdminOTPToken,
            AdminOTPToken.email == settings.admin_email,
        )
        if not tokens:
            raise NotFoundServiceError("No admin OTP session exists. Start sign in again.")

        latest_token = max(tokens, key=lambda token: token.created_at)
        now = datetime.now(timezone.utc)

        if latest_token.is_used:
            raise AuthenticationServiceError("The OTP has already been used.")

        expires_at = latest_token.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at is None or expires_at < now:
            raise AuthenticationServiceError("The OTP has expired. Request a new one.")
        if latest_token.otp_code_hash != self._hash_otp(otp_code):
            raise AuthenticationServiceError("The OTP provided is invalid.")

        latest_token.is_used = True
        await engine.save(latest_token)
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
        upper_bound = 10 ** settings.customer_otp_length
        otp_code = f"{secrets.randbelow(upper_bound):0{settings.customer_otp_length}d}"
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.customer_otp_expiry_minutes
        )

        token = OTPToken(
            mobile_number=normalized_mobile,
            otp_code_hash=self._hash_otp(otp_code),
            purpose=purpose,
            is_used=False,
            expires_at=expires_at,
        )
        await engine.save(token)

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

        latest_token = max(tokens, key=lambda token: token.created_at)
        now = datetime.now(timezone.utc)

        if latest_token.is_used:
            raise AuthenticationServiceError("The OTP has already been used.")

        # Ensure expires_at is timezone-aware before comparison
        expires_at = latest_token.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at is None or expires_at < now:
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


auth_service = AuthService()

