# InsureFlow Architecture Documentation

## 1. Product Summary

InsureFlow is a broker-led insurance platform. It provides a single customer journey for insurance purchase while separating backend responsibilities across Main Backend and Provider Backend.

The customer does not choose a broker. Broker onboarding is handled by admin-only APIs and broker API keys.

## 2. System Components

### Frontend

Responsibilities:

- customer application form
- quote comparison
- add-on selection
- payment checkout launch
- customer dashboard
- policy and receipt download
- support ticket UI
- admin dashboard

### Main Backend

Responsibilities:

- customer authentication
- admin authentication
- application lifecycle
- active journey resume
- transaction ledger
- normalized quote storage
- quote selection and add-on update
- payment initiation coordination
- provider webhook sync
- customer dashboard
- admin dashboard
- support tickets
- audit logs

### Provider Backend

Responsibilities:

- provider registration
- broker API-key registry
- insurance plan catalog
- add-on catalog
- provider-side transaction tracking
- quote generation
- payment session creation
- payment verification
- policy issuance
- receipt generation
- policy document generation
- webhook retry

## 3. Backend Ownership

| Domain | Owner |
|---|---|
| Customer login | Main Backend |
| Admin login | Main Backend |
| Broker API-key registration | Provider Backend, initiated through Main Backend admin API |
| Application storage | Main Backend |
| Transaction source of truth | Main Backend |
| Provider execution transaction | Provider Backend |
| Insurance details | Main Backend |
| Quote generation | Provider Backend |
| Normalized quote storage | Main Backend |
| Payment order/session creation | Provider Backend |
| Payment status sync | Provider Backend to Main Backend |
| Policy generation | Provider Backend |
| Dashboard | Main Backend |

## 4. Customer Journey

```txt
User visits frontend
→ selects insurance type
→ fills application details without login
→ Main Backend checks active journey
→ Main Backend creates application, transaction, insurance_details
→ Main Backend requests quotes from Provider Backend
→ Provider Backend creates provider_transaction and provider_quotes
→ Main Backend stores normalized quotes
→ Frontend shows quotes
→ User selects quote
→ User selects add-ons
→ Main Backend updates transaction final amount
→ User clicks Pay
→ Main Backend requests payment session from Provider Backend
→ Provider Backend creates gateway order/session
→ Frontend opens payment checkout
→ Provider Backend verifies payment success
→ Provider Backend generates receipt and policy
→ Provider Backend syncs status to Main Backend
→ User views policy and receipt from dashboard
```

## 5. Broker Registration Flow

Broker registration is admin-only.

```txt
Admin logs in
→ Admin verifies 2FA
→ Admin receives ADMIN JWT
→ Admin submits broker details
→ Main Backend validates ADMIN JWT
→ Main Backend forwards broker registration request to Provider Backend
→ Provider Backend generates broker API key
→ Provider Backend stores api_key_hash
→ Provider Backend returns plain API key once
→ Admin securely shares key with broker
```

Broker registration data:

```txt
broker_code
broker_name
api_key_hash
callback_url
webhook_url
status
created_by_admin
created_at
updated_at
```

Plain API key must not be stored.

## 6. API Key Generation

Provider Backend should generate broker API keys using secure randomness.

Example:

```py
import secrets
import hashlib

def generate_broker_api_key() -> str:
    return f"brk_live_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
```

Only `api_key_hash` is stored.

## 7. Model Documentation

### Main Backend Models

#### users

Information stored:

```txt
full_name
email
mobile_number
password hash for admin users
user_role CUSTOMER or ADMIN
is_verified
is_active
created_at
updated_at
```

Description:

Stores customer and admin identities. Admin is a `User` with `user_role = ADMIN`.

#### otp_tokens

Information stored:

```txt
mobile_number
otp_code hash
purpose LOGIN / REGISTER / ADMIN_2FA
is_used
created_at
expires_at
```

Description:

Stores OTP verification sessions. Plain OTP is printed only in backend logs during local development.

#### applications

Information stored:

```txt
application_reference
user_id or guest identifier
transaction_id
transaction_reference
insurance_type
personal_details
health_details
coverage_details
nominee_details
application_status
created_at
updated_at
```

Description:

Stores the submitted application. Used to resume an active customer journey by mobile number and insurance type.

#### transactions

Information stored:

```txt
transaction_reference
application_id
insurance_details_id
selected_quote_id
selected_addons
base_premium
addon_amount
final_amount
transaction_status
payment_status
policy_status
provider_transaction_reference
provider_payment_reference
provider_policy_reference
payment_url or checkout metadata
created_at
updated_at
```

Description:

Main business ledger connecting application, insurance details, selected quote, add-ons, payment, and policy.

#### insurance_details

Information stored:

```txt
transaction_reference
insurance_type
coverage_amount
tenure
sum_insured
insured_members
health_details
vehicle_details
travel_details
home_details
life_details
nominee_details
created_at
updated_at
```

Description:

Stores insurance-specific details separately from transaction. This avoids putting health, car, travel, home, and life-specific fields directly into the transaction model.

#### quotes

Information stored:

```txt
transaction_reference
transaction_id
provider_quote_id
provider_name
plan_code
plan_name
base_premium
tax_amount
total_premium
coverage_amount
available_addons
quote_status
expires_at
created_at
```

Description:

Stores normalized quote options returned by Provider Backend. Used for comparison, resume, and quote selection.

#### tickets

Information stored:

```txt
ticket_reference
user_id
transaction_reference
category
priority
status
subject
message
assigned_admin_id
admin_response
created_at
updated_at
```

Description:

Stores customer support tickets and admin resolution workflow.

#### audit_logs

Information stored:

```txt
actor_id
actor_role
action
entity_type
entity_id
transaction_reference
old_state
new_state
created_at
```

Description:

Stores admin and system action history for traceability.

#### webhook_events

Information stored:

```txt
event_type
transaction_reference
provider_payment_reference
provider_policy_reference
payload
processing_status
received_at
processed_at
```

Description:

Stores inbound provider sync events for payment and policy updates.

### Provider Backend Models

#### providers

Information stored:

```txt
provider_code
provider_name
contact_email
contact_phone
webhook_url
status
created_at
updated_at
```

Description:

Stores insurer/provider companies that generate quotes and issue policies.

#### broker_registry

Information stored:

```txt
broker_code
broker_name
api_key_hash
callback_url
webhook_url
status
created_by_admin
last_key_rotated_at
created_at
updated_at
```

Description:

Stores admin-registered broker access. API key is generated by Provider Backend and stored only as a hash.

#### insurance_plans

Information stored:

```txt
plan_code
provider_code
insurance_type
plan_name
coverage_options
base_premium_rules
benefits
status
created_at
updated_at
```

Description:

Stores provider plan catalog used during quote generation.

#### addons

Information stored:

```txt
addon_code
provider_code
insurance_type
addon_name
addon_description
addon_price
status
created_at
updated_at
```

Description:

Stores optional riders that update the final payable amount before payment.

#### provider_transactions

Information stored:

```txt
provider_transaction_reference
main_transaction_reference
provider_code
broker_code
application_reference
insurance_type
quote_reference
payment_reference
policy_reference
gateway_order_id
gateway_payment_id
execution_status
created_at
updated_at
```

Description:

Provider-side execution tracker linked to the Main Backend transaction. It should not duplicate the entire Main transaction.

#### provider_quotes

Information stored:

```txt
provider_transaction_reference
main_transaction_reference
provider_quote_id
plan_code
base_premium
tax_amount
total_premium
coverage_amount
risk_score
risk_category
available_addons
status
expires_at
created_at
```

Description:

Stores raw provider-generated quote options before Main Backend normalizes them for frontend display.

#### payments

Information stored:

```txt
payment_reference
provider_transaction_reference
main_transaction_reference
gateway_name
gateway_order_id
gateway_payment_id
gateway_signature
amount
currency
payment_status
receipt_pdf_path
receipt_document_url
created_at
updated_at
```

Description:

Stores gateway payment order/session and payment verification result.

#### policies

Information stored:

```txt
policy_number
provider_transaction_reference
main_transaction_reference
payment_reference
provider_quote_id
policy_status
coverage_amount
premium_amount
issue_date
start_date
end_date
policy_pdf_path
policy_document_url
created_at
updated_at
```

Description:

Stores issued policy details and document link. Created only after successful verified payment.

#### webhook_retries

Information stored:

```txt
event_type
main_transaction_reference
payload
retry_count
next_retry_at
status
last_error
created_at
updated_at
```

Description:

Stores failed sync attempts from Provider Backend to Main Backend for retry.

## 8. Status Flow

Recommended transaction statuses:

```txt
APPLICATION_SUBMITTED
QUOTE_GENERATED
QUOTE_SELECTED
PAYMENT_PENDING
PAYMENT_SUCCESS
PAYMENT_FAILED
POLICY_ISSUED
EXPIRED
REJECTED
CANCELLED
```

Active journey statuses:

```txt
APPLICATION_SUBMITTED
QUOTE_GENERATED
QUOTE_SELECTED
PAYMENT_PENDING
```

Closed statuses:

```txt
POLICY_ISSUED
PAYMENT_FAILED
EXPIRED
REJECTED
CANCELLED
```

## 9. API Sequence Summary

Customer:

```txt
POST /api/v1/applications
POST /api/v1/quotes/select/{quote_id}
POST /api/v1/payments/initiate/{transaction_reference}
GET /api/v1/payments/status/{transaction_reference}
GET /api/v1/policies/me
GET /api/v1/policies/{policy_number}/download
```

Main to Provider:

```txt
POST /api/v1/quotes/generate
POST /api/v1/payments/create-session
POST /api/v1/provider-sync/webhook
```

Admin:

```txt
POST /api/v1/admin/brokers
GET /api/v1/admin/brokers
PATCH /api/v1/admin/brokers/{broker_code}/status
PUT /api/v1/admin/brokers/{broker_code}/rotate-key
GET /api/v1/admin/transactions
GET /api/v1/admin/policies
GET /api/v1/admin/payments
```

