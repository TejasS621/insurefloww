"""Payment creation request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PaymentSessionCreateRequest(BaseModel):
    """Create a payment order or checkout session."""

    model_config = ConfigDict(extra="forbid")

    provider_transaction_reference: str = Field(..., min_length=3, max_length=100)
    main_transaction_reference: str = Field(..., min_length=3, max_length=100)
    provider_quote_id: str = Field(..., min_length=3, max_length=100)
    selected_addons: list[str] = Field(default_factory=list)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)


class PaymentCustomerDetailsRequest(BaseModel):
    """Customer details required to personalize a hosted payment session."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=2, max_length=120, description="Customer full name.")
    email: EmailStr = Field(..., description="Customer email address.")
    mobile_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Customer mobile number used during checkout.",
    )


class MockPaymentCreateRequest(BaseModel):
    """Create a mock hosted payment session for frontend redirection."""

    model_config = ConfigDict(extra="forbid")

    transaction_reference: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Main backend transaction reference for this payment attempt.",
    )
    quote_reference: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Selected quote reference associated with the payment.",
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Final payable amount for the selected insurance quote.",
    )
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="Currency code for the payment session.",
    )
    customer: PaymentCustomerDetailsRequest = Field(
        ...,
        description="Customer details shown during the hosted payment experience.",
    )
    selected_payment_method: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        description="Optional payment method preselected by the frontend.",
    )

