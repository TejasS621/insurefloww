# InsureFlow MCP Server

This package provides a production-oriented Model Context Protocol server for InsureFlow.

The server is intentionally thin:
- validates MCP tool inputs
- calls existing InsureFlow REST APIs
- reshapes backend responses into MCP-friendly results
- applies retries, timeouts, and structured error handling

It does **not** implement underwriting, quote generation, payment processing, policy issuance, or ticket business logic.

## Folder Layout

```text
mcp/
  tests/
  .env.example
  README.md
  requirements.txt
insureflow_mcp/
  clients/
  core/
  schemas/
  tools/
mcp_server.py
```

## Supported Tools

- `request_customer_otp`
- `verify_customer_otp`
- `admin_login`
- `admin_verify`
- `generate_quote`
- `select_quote`
- `initiate_payment`
- `get_payment_status`
- `get_policy`
- `download_policy`
- `create_ticket`
- `list_brokers`
- `register_broker`

## Important Backend Alignment Notes

- `generate_quote` calls `POST /api/v1/applications`
- `request_customer_otp` calls `POST /api/v1/auth/login/otp`
- `verify_customer_otp` calls `POST /api/v1/auth/login/verify`
- `admin_login` calls `POST /api/v1/auth/admin/login`
- `admin_verify` calls `POST /api/v1/auth/admin/login/verify`
- `register_broker` requires `broker_code` because the backend admin API requires it
- Tools only wrap backend routes that exist directly today; no missing route emulation is performed

## Setup

1. Create or activate a Python 3.12+ virtual environment.
2. Install dependencies:

```powershell
pip install -r mcp/requirements.txt
```

3. Copy the example environment file:

```powershell
Copy-Item mcp/.env.example .env
```

4. Start the MCP server:

```powershell
python mcp_server.py
```

## Authentication Model

- Guest-compatible tools:
  - `generate_quote`
  - `select_quote`
  - `initiate_payment`
  - `get_payment_status`

- Customer-authenticated tools require a prior `verify_customer_otp` call:
  - `get_policy`
  - `download_policy`
  - `create_ticket`

- Admin-authenticated tools require a prior `admin_login` or `admin_verify` call:
  - `list_brokers`
  - `register_broker`

The MCP server stores the latest customer and admin tokens in its own in-memory
session after successful login tools. Static JWT environment variables are not used.

## Claude Desktop Configuration

Use the absolute path for your local environment. Example:

```json
{
  "mcpServers": {
    "insureflow": {
      "command": "C:\\InsureFloww\\venv\\Scripts\\python.exe",
      "args": ["C:\\InsureFloww\\mcp_server.py"],
      "env": {
        "MAIN_BACKEND_URL": "http://localhost:8000/api/v1",
        "MCP_REQUEST_TIMEOUT_SECONDS": "15",
        "MCP_MAX_RETRIES": "2",
        "MCP_RETRY_BACKOFF_SECONDS": "0.5",
        "MCP_DOWNLOAD_DIRECTORY": "storage/mcp_downloads",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

If you prefer a project-local Python install, change the `command` path to the correct interpreter.

## Production Deployment Notes

- Run the server with a dedicated service account and tightly scoped environment variables.
- Treat the in-memory MCP auth session as process-local and restart the server to clear it.
- Keep the MCP server close to the backends to reduce request latency.
- Use centralized log aggregation for the structured logs emitted by the server.

## Test Suite

Run the unit tests with:

```powershell
python -m pytest mcp/tests
```
