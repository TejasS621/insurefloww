"""Pipecat function registration for InsureFlow voice workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from insureflow_mcp.core.results import ToolResult
from insureflow_mcp.schemas.auth import RequestCustomerOTPInput, VerifyCustomerOTPInput
from insureflow_mcp.schemas.payments import GetPaymentStatusInput, InitiatePaymentInput
from insureflow_mcp.schemas.policies import DownloadPolicyInput, GetPolicyInput
from insureflow_mcp.schemas.quotes import GenerateQuoteInput, SelectQuoteInput
from insureflow_mcp.schemas.tickets import CreateTicketInput
from voice_bot.runtime import VoiceBotRuntime

try:
    from pipecat.adapters.schemas.function_schema import FunctionSchema
    from pipecat.adapters.schemas.tools_schema import ToolsSchema
    from pipecat.services.llm_service import FunctionCallParams
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    raise RuntimeError(
        "Pipecat dependencies are not installed. Install voice_bot/requirements.txt first."
    ) from exc


ToolHandler = Callable[[BaseModel], Awaitable[ToolResult[Any]]]


class VoiceGetPolicyInput(BaseModel):
    """Policy lookup input that hides JWT session details from the caller."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str = Field(
        ...,
        description="Policy number to fetch from InsureFlow for the authenticated customer.",
    )


class VoiceDownloadPolicyInput(BaseModel):
    """Policy-download input that hides JWT session details from the caller."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str = Field(
        ...,
        description="Policy number whose PDF should be downloaded for the authenticated customer.",
    )


class VoiceCreateTicketInput(BaseModel):
    """Ticket-creation input that hides JWT session details from the caller."""

    model_config = ConfigDict(extra="forbid")

    transaction_reference: str | None = Field(
        default=None,
        description="Optional transaction reference if the support issue is tied to a specific purchase journey.",
    )
    category: str = Field(
        default="GENERAL",
        description="Ticket category such as CLAIM, PAYMENT, POLICY, or GENERAL.",
    )
    priority: str = Field(
        default="MEDIUM",
        description="Ticket priority such as LOW, MEDIUM, or HIGH.",
    )
    subject: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Short subject that summarizes the support request.",
    )
    message: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Detailed support message describing what the customer needs help with.",
    )


@dataclass(slots=True)
class VoiceToolDefinition:
    """Metadata required to expose an MCP-backed workflow to the LLM."""

    name: str
    description: str
    input_model: type[BaseModel]
    handler: ToolHandler

    def to_function_schema(self) -> FunctionSchema:
        """Convert the underlying Pydantic input model into a Pipecat tool schema."""

        schema = _build_gemini_friendly_schema(self.input_model)
        return FunctionSchema(
            name=self.name,
            description=self.description,
            properties=schema.get("properties", {}),
            required=schema.get("required", []),
        )


def build_voice_tool_definitions(runtime: VoiceBotRuntime) -> list[VoiceToolDefinition]:
    """Create the supported customer workflow tool definitions."""

    return [
        VoiceToolDefinition(
            name="request_customer_otp",
            description="Request a customer login OTP using the customer's mobile number.",
            input_model=RequestCustomerOTPInput,
            handler=runtime.auth_tools.request_customer_otp,
        ),
        VoiceToolDefinition(
            name="verify_customer_otp",
            description="Verify the customer OTP and store the customer access token in session.",
            input_model=VerifyCustomerOTPInput,
            handler=runtime.auth_tools.verify_customer_otp,
        ),
        VoiceToolDefinition(
            name="generate_quote",
            description=(
                "Create an insurance application and generate quote options. "
                "Use this when the customer wants a new quote."
            ),
            input_model=GenerateQuoteInput,
            handler=runtime.quote_tools.generate_quote,
        ),
        VoiceToolDefinition(
            name="select_quote",
            description="Select an existing quote and return the updated pricing details.",
            input_model=SelectQuoteInput,
            handler=runtime.quote_tools.select_quote,
        ),
        VoiceToolDefinition(
            name="initiate_payment",
            description="Start the hosted payment flow for a selected transaction reference.",
            input_model=InitiatePaymentInput,
            handler=runtime.payment_tools.initiate_payment,
        ),
        VoiceToolDefinition(
            name="get_payment_status",
            description="Check the current payment status for a transaction reference.",
            input_model=GetPaymentStatusInput,
            handler=runtime.payment_tools.get_payment_status,
        ),
        VoiceToolDefinition(
            name="get_policy",
            description=(
                "Fetch policy details for the customer currently authenticated in this voice session. "
                "Do not ask the customer for a token."
            ),
            input_model=VoiceGetPolicyInput,
            handler=lambda payload: runtime.get_policy_with_session(
                GetPolicyInput(
                    policy_number=payload.policy_number,
                    customer_access_token="session",
                )
            ),
        ),
        VoiceToolDefinition(
            name="download_policy",
            description=(
                "Download a policy PDF for the customer currently authenticated in this voice session. "
                "Do not ask the customer for a token."
            ),
            input_model=VoiceDownloadPolicyInput,
            handler=lambda payload: runtime.download_policy_with_session(
                DownloadPolicyInput(
                    policy_number=payload.policy_number,
                    customer_access_token="session",
                )
            ),
        ),
        VoiceToolDefinition(
            name="create_ticket",
            description=(
                "Create a customer support ticket for policy, payment, claim, or general help "
                "for the customer currently authenticated in this voice session."
            ),
            input_model=VoiceCreateTicketInput,
            handler=lambda payload: runtime.create_ticket_with_session(
                CreateTicketInput(
                    customer_access_token="session",
                    transaction_reference=payload.transaction_reference,
                    category=payload.category,
                    priority=payload.priority,
                    subject=payload.subject,
                    message=payload.message,
                )
            ),
        ),
    ]


def build_tools_schema(definitions: list[VoiceToolDefinition]) -> ToolsSchema:
    """Build the Pipecat tool schema bundle for the LLM context."""

    return ToolsSchema(standard_tools=[definition.to_function_schema() for definition in definitions])


def register_voice_tools(
    *,
    llm: Any,
    definitions: list[VoiceToolDefinition],
) -> None:
    """Register all voice bot functions with the Pipecat LLM service."""

    for definition in definitions:
        llm.register_function(definition.name, _build_callback(definition))


def _build_callback(definition: VoiceToolDefinition) -> Callable[[FunctionCallParams], Awaitable[None]]:
    """Wrap an MCP-backed tool so Pipecat can invoke it from a function call."""

    async def callback(params: FunctionCallParams) -> None:
        try:
            arguments = _extract_arguments(params)
        except ValueError as exc:
            await params.result_callback(
                {
                    "success": False,
                    "message": "I could not understand the tool arguments for that request.",
                    "error": {
                        "code": "invalid_tool_arguments",
                        "detail": str(exc),
                        "status_code": 422,
                        "retryable": False,
                    },
                }
            )
            return

        try:
            payload = definition.input_model.model_validate(arguments)
        except ValidationError as exc:
            await params.result_callback(_validation_error_payload(exc))
            return

        try:
            result = await definition.handler(payload)
        except Exception as exc:  # pragma: no cover - defensive voice runtime guard
            await params.result_callback(
                {
                    "success": False,
                    "message": "The InsureFlow voice tool failed unexpectedly.",
                    "error": {
                        "code": "voice_tool_runtime_error",
                        "detail": str(exc),
                        "status_code": 500,
                        "retryable": False,
                    },
                }
            )
            return

        await params.result_callback(result.model_dump(mode="json"))

    return callback


def _extract_arguments(params: FunctionCallParams) -> dict[str, Any]:
    """Normalize Pipecat function-call arguments into a Python dictionary."""

    for attribute_name in ("arguments", "args", "parameters"):
        value = getattr(params, attribute_name, None)
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError("The tool arguments were not valid JSON.") from exc
    return {}


def _validation_error_payload(exc: ValidationError) -> dict[str, Any]:
    """Return a consistent user-facing validation error payload."""

    error_messages = [
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors(include_url=False)
    ]
    detail = "; ".join(error_messages) or "Missing or invalid input."
    return {
        "success": False,
        "message": "I need a few more details before I can complete that request.",
        "error": {
            "code": "validation_failed",
            "detail": detail,
            "status_code": 422,
            "retryable": False,
        },
    }


def _build_gemini_friendly_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model schema into a flattened Gemini-friendly JSON schema."""

    raw_schema = model.model_json_schema()
    definitions = raw_schema.get("$defs", {})

    return _sanitize_schema_node(raw_schema, definitions)


def _sanitize_schema_node(node: Any, definitions: dict[str, Any]) -> Any:
    """Recursively inline refs and strip unsupported JSON schema keywords."""

    if isinstance(node, list):
        return [_sanitize_schema_node(item, definitions) for item in node]

    if not isinstance(node, dict):
        return node

    if "$ref" in node:
        ref_name = str(node["$ref"]).split("/")[-1]
        resolved = definitions.get(ref_name, {})
        return _sanitize_schema_node(resolved, definitions)

    if "anyOf" in node:
        variants = [
            _sanitize_schema_node(variant, definitions)
            for variant in node["anyOf"]
            if not (isinstance(variant, dict) and variant.get("type") == "null")
        ]
        if len(variants) == 1:
            return variants[0]
        return {"anyOf": variants}

    sanitized: dict[str, Any] = {}
    for key, value in node.items():
        if key in {"$defs", "$ref", "default", "title", "examples"}:
            continue
        if key == "properties" and isinstance(value, dict):
            sanitized[key] = {
                prop_name: _sanitize_schema_node(prop_value, definitions)
                for prop_name, prop_value in value.items()
            }
            continue
        if key == "items":
            sanitized[key] = _sanitize_schema_node(value, definitions)
            continue
        sanitized[key] = _sanitize_schema_node(value, definitions)

    return sanitized
