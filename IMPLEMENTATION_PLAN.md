# InsureFlow Implementation Plan

This plan is for restarting InsureFlow in a new folder with the updated architecture.

## Phase 1: Project Setup

Create the project structure:

```txt
insureflow/
  frontend/
  backend/
    main_backend/
    provider_backend/
  docs/
    adr/
```

Recommended backend structure:

```txt
backend/main_backend/
  app/
    api/routes/
    api/schemas/requests/
    api/schemas/responses/
    core/
    models/
    services/
    cruds/
    utils/

backend/provider_backend/
  app/
    api/routes/
    api/schemas/requests/
    api/schemas/responses/
    core/
    models/
    services/
    cruds/
    utils/
```

## Phase 2: Authentication

Implement customer authentication:

```txt
POST /api/v1/auth/login/otp
POST /api/v1/auth/login/verify
```

Rules:

- Customer logs in by mobile OTP.
- OTP is hashed in DB.
- Plain OTP appears only in backend logs for local development.
- Frontend must not display OTP preview.

Implement admin authentication:

```txt
POST /api/v1/auth/admin/login
POST /api/v1/auth/admin/login/verify
```

Rules:

- Admin logs in with email/password.
- Admin verifies 2FA OTP.
- Admin receives ADMIN JWT.
- Admin APIs require `Authorization: Bearer <ADMIN_TOKEN>`.

Use `users` collection with:

```txt
user_role = CUSTOMER | ADMIN
```

Do not create a separate admin model initially.

## Phase 3: Admin Broker Registration

Customer should not select broker.

Admin registers a broker before operational use:

```txt
Admin Frontend
→ Main Backend
→ Provider Backend
```

Main Backend APIs:

```txt
POST /api/v1/admin/brokers
GET /api/v1/admin/brokers
PATCH /api/v1/admin/brokers/{broker_code}/status
PUT /api/v1/admin/brokers/{broker_code}/rotate-key
```

Provider Backend APIs:

```txt
POST /api/v1/provider/brokers/register
GET /api/v1/provider/brokers
PATCH /api/v1/provider/brokers/{broker_code}/status
PUT /api/v1/provider/brokers/{broker_code}/rotate-key
```

Broker registration request:

```json
{
  "broker_name": "Clic360",
  "broker_code": "CLIC360",
  "callback_url": "https://clic360.example.com/callback",
  "webhook_url": "https://clic360.example.com/webhook"
}
```

Provider Backend generates API key:

```txt
brk_live_<secure_random_token>
```

Provider Backend stores only:

```txt
api_key_hash
```

Response returns the plain API key once:

```json
{
  "broker_code": "CLIC360",
  "api_key": "brk_live_xxxxx",
  "message": "Save this API key now. It will not be shown again."
}
```

## Phase 4: Main Customer Application Flow

Frontend submits:

```txt
POST /api/v1/applications
```

Main Backend should:

1. Read mobile number and insurance type.
2. Check active journey for:

```txt
mobile_number + insurance_type + active_status
```

Active statuses:

```txt
APPLICATION_SUBMITTED
QUOTE_GENERATED
QUOTE_SELECTED
PAYMENT_PENDING
```

3. If active journey exists:

```txt
return existing application + transaction + quotes
```

4. If no active journey exists:

```txt
create application
create transaction
create insurance_details
call Provider Backend for quotes
store normalized quotes
return application + transaction + quotes
```

Allow new journey when previous status is:

```txt
POLICY_ISSUED
PAYMENT_FAILED
EXPIRED
REJECTED
CANCELLED
```

## Phase 5: Quote Generation

Quote generation is owned by Provider Backend.

Main Backend calls:

```txt
POST /api/v1/provider/quotes/generate
```

Provider Backend should:

1. Create or fetch `provider_transaction`.
2. Read insurance details.
3. Match plans and add-ons.
4. Calculate premiums.
5. Store `provider_quotes`.
6. Return quote options.

Main Backend should:

1. Normalize provider quotes.
2. Store them in `quotes`.
3. Return quotes to frontend.

## Phase 6: Quote Selection And Add-ons

Frontend calls:

```txt
POST /api/v1/quotes/select/{quote_id}
```

Main Backend updates `transactions`:

```txt
selected_quote_id
selected_addons
base_premium
addon_amount
final_amount
transaction_status = QUOTE_SELECTED
```

## Phase 7: Payment Gateway

Frontend calls:

```txt
POST /api/v1/payments/initiate/{transaction_reference}
```

Main Backend:

- validates transaction
- validates selected quote
- sends selected quote, add-ons, and final amount to Provider Backend
- does not create payment URL/order

Provider Backend:

- creates Razorpay or other gateway order/session
- stores payment reference
- returns checkout details

Provider Backend returns:

```json
{
  "gateway": "RAZORPAY",
  "razorpay_key_id": "rzp_test_xxxxx",
  "razorpay_order_id": "order_xxxxx",
  "provider_payment_reference": "PAY-xxxxx",
  "amount": 120000,
  "currency": "INR"
}
```

Frontend opens Razorpay checkout.

## Phase 8: Payment Success And Policy Generation

Payment success callback goes to Provider Backend:

```txt
POST /api/v1/provider/webhooks/payment-success
```

Provider Backend:

1. verifies payment signature
2. marks payment success
3. generates receipt
4. generates policy
5. generates policy document
6. syncs status to Main Backend

Main Backend sync endpoint:

```txt
POST /api/v1/provider-sync/webhook
```

Main Backend updates:

```txt
transaction_status
payment_status
policy_status
provider_payment_reference
provider_policy_reference
```

## Phase 9: Dashboard And Documents

Customer dashboard APIs:

```txt
GET /api/v1/applications/me
GET /api/v1/policies/me
GET /api/v1/policies/{policy_number}
GET /api/v1/policies/{policy_number}/download
GET /api/v1/payments/status/{transaction_reference}
GET /api/v1/payments/receipt/{transaction_reference}
GET /api/v1/payments/receipt/{transaction_reference}/download
```

Admin dashboard APIs:

```txt
GET /api/v1/admin/dashboard
GET /api/v1/admin/applications
GET /api/v1/admin/customers
GET /api/v1/admin/transactions
GET /api/v1/admin/quotes
GET /api/v1/admin/payments
GET /api/v1/admin/policies
GET /api/v1/admin/tickets
```

## Phase 10: Support And Audit

Customer:

```txt
POST /api/v1/tickets
GET /api/v1/tickets/me
```

Admin:

```txt
GET /api/v1/admin/tickets
PUT /api/v1/admin/tickets/{ticket_id}/assign
PUT /api/v1/admin/tickets/{ticket_id}/status
```

Audit logs should record:

```txt
actor_id
actor_role
action
entity_type
entity_id
old_state
new_state
transaction_reference
created_at
```

