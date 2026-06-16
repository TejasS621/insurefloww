"""
Implement OTP-based authentication helpers for the main backend.

Args:
    None: This module defines the service layer for customer and admin OTP
    generation, validation, and credential checks.

Returns:
    None: Service methods return typed OTP dispatch data, persisted token
    records, or authenticated identity values.

Raises:
    ServiceError: Authentication and lookup errors are raised when OTP or
    credential validation fails.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from odmantic import AIOEngine

from backend.main_backend.commons.config import settings
from backend.main_backend.commons.logger import get_logger
from backend.main_backend.core.models.user_model import (
    AdminOTPToken,
    OTPPurpose,
    OTPToken,
)

from .service_exceptions import AuthenticationServiceError, NotFoundServiceError

logger = get_logger(__name__)


@dataclass(slots=True)
class OTPDispatchResult:
    """Represents a generated OTP ready for out-of-band delivery."""

    mobile_number: str
    otp_code: str
    expires_at: datetime
    purpose: OTPPurpose


class AuthService:
    """
    Encapsulate OTP-centric authentication helper workflows.

    Args:
        None: Service state is derived from configuration and database inputs.

    Returns:
        None: Instance methods return typed auth workflow results.

    Raises:
        ServiceError: Authentication and lookup failures are surfaced as
        domain-specific service exceptions.
    """

    async def authenticate_admin_credentials(self, *, email: str, password: str) -> str:
        """
        Validate configured admin credentials and return the admin identity.

        Args:
            email: Submitted admin email address.
            password: Submitted admin password.

        Returns:
            str: Canonical admin email address used as the authenticated identity.

        Raises:
            AuthenticationServiceError: Raised when the supplied credentials do
            not match the configured admin account.
        """
        if email.strip().lower() != settings.admin_email.strip().lower():
            logger.warning("Rejected admin credential authentication for '%s'.", email)
            raise AuthenticationServiceError("The supplied admin credentials are invalid.")
        if password != settings.admin_password:
            logger.warning("Rejected admin credential authentication for '%s'.", email)
            raise AuthenticationServiceError("The supplied admin credentials are invalid.")
        return settings.admin_email

    async def request_admin_otp(
        self,
        engine: AIOEngine,
        *,
        email: str,
    ) -> OTPDispatchResult:
        """
        Create and persist a one-time-password for the admin sign-in flow.

        Args:
            engine: Active ODMantic database engine dependency.
            email: Admin email address to verify before issuing the OTP.

        Returns:
            OTPDispatchResult: Generated OTP metadata for the admin challenge.

        Raises:
            AuthenticationServiceError: Raised when the admin identity is invalid.
        """
        if email.strip().lower() != settings.admin_email.strip().lower():
            raise AuthenticationServiceError(
                "The supplied admin verification details are invalid."
            )

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
        logger.info("Generated admin OTP challenge for '%s'.", settings.admin_email)

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
        """
        Validate the latest admin OTP challenge and return the admin identity.

        Args:
            engine: Active ODMantic database engine dependency.
            email: Admin email address tied to the OTP challenge.
            otp_code: OTP code submitted by the admin user.

        Returns:
            str: Canonical admin email after successful OTP verification.

        Raises:
            AuthenticationServiceError: Raised when the OTP is invalid, used,
            or expired.
            NotFoundServiceError: Raised when no admin OTP session exists.
        """
        normalized_email = email.strip().lower()
        if normalized_email != settings.admin_email.strip().lower():
            raise AuthenticationServiceError(
                "The supplied admin verification details are invalid."
            )

        tokens = await engine.find(
            AdminOTPToken,
            AdminOTPToken.email == settings.admin_email,
        )
        if not tokens:
            logger.warning("No admin OTP session found for '%s'.", email)
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
        logger.info("Verified admin OTP for '%s'.", settings.admin_email)
        return settings.admin_email

    async def request_customer_otp(
        self,
        engine: AIOEngine,
        mobile_number: str,
        *,
        purpose: OTPPurpose = OTPPurpose.LOGIN,
    ) -> OTPDispatchResult:
        """
        Create and persist a one-time-password for customer login.

        Args:
            engine: Active ODMantic database engine dependency.
            mobile_number: Customer mobile number used for OTP delivery.
            purpose: OTP purpose used to scope the challenge type.

        Returns:
            OTPDispatchResult: Generated OTP metadata for the customer challenge.

        Raises:
            AuthenticationServiceError: Raised when the mobile number is invalid.
        """
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
        logger.info(
            "Generated customer OTP challenge for '%s' with purpose '%s'.",
            normalized_mobile,
            purpose.value,
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
        """
        Validate a customer OTP and mark the matching token as used.

        Args:
            engine: Active ODMantic database engine dependency.
            mobile_number: Customer mobile number tied to the OTP challenge.
            otp_code: OTP code submitted by the customer.
            purpose: OTP purpose used to scope token lookup.

        Returns:
            OTPToken: Persisted OTP token after successful verification.

        Raises:
            AuthenticationServiceError: Raised when the OTP is invalid, used,
            expired, or the mobile number is malformed.
            NotFoundServiceError: Raised when no OTP session exists.
        """
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
        """
        Normalize a mobile number into a digits-only local format.

        Args:
            mobile_number: Raw mobile number input from a caller or payload.

        Returns:
            str: Normalized digits-only mobile number.

        Raises:
            AuthenticationServiceError: Raised when the value does not contain
            enough digits to represent a valid mobile number.
        """
        normalized = "".join(character for character in mobile_number if character.isdigit())
        if len(normalized) < 10:
            raise AuthenticationServiceError("A valid mobile number is required.")
        return normalized

    @staticmethod
    def _hash_otp(otp_code: str) -> str:
        """
        Hash an OTP value before storing it in persistence.

        Args:
            otp_code: Plain-text OTP generated for a login challenge.

        Returns:
            str: SHA-256 hash of the supplied OTP value.

        Raises:
            ValueError: Propagates if hashing input is not valid text.
        """
        return hashlib.sha256(otp_code.encode("utf-8")).hexdigest()


auth_service = AuthService()
