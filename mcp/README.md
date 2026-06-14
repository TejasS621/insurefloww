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

- Customer journey tools:
  - `request_customer_otp`
  - `verify_customer_otp`
  - `generate_quote`
  - `select_quote`
  - `initiate_payment`
  - `get_payment_status`
  - `get_policy`
  - `download_policy`
  - `create_ticket`
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

4. Start the local stdio MCP server for Claude Desktop:

```powershell
python mcp_server.py
```

5. Start the remote HTTP MCP server:

```powershell
$env:MCP_TRANSPORT="http"
python mcp_remote_server.py
```

Default remote bind settings:
- `MCP_HOST=0.0.0.0`
- `MCP_PORT=8080`
- `MCP_HTTP_PATH=/mcp`
- `MCP_HEALTH_PATH=/health`

The remote health check will be available at:
- `http://localhost:8080/health`

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

## Remote HTTP Configuration

Remote deployments use the same MCP tool set and the same thin orchestration layer. No business logic is duplicated.

Environment variables:
- `MCP_TRANSPORT=stdio|http`
- `MCP_HOST=0.0.0.0`
- `MCP_PORT=8080`
- `MCP_HTTP_PATH=/mcp`
- `MCP_HEALTH_PATH=/health`
- `MCP_CORS_ALLOW_ORIGINS=["*"]`

Local remote run:

```powershell
$env:MCP_TRANSPORT="http"
$env:MCP_HOST="0.0.0.0"
$env:MCP_PORT="8080"
python mcp_remote_server.py
```

The FastMCP server uses streamable HTTP for the remote endpoint path configured by `MCP_HTTP_PATH`.

## Deployment Notes

Railway:
- Set the start command to `python mcp_remote_server.py`
- Set `MCP_TRANSPORT=http`
- Set `MCP_HOST=0.0.0.0`
- Set `MCP_PORT` to Railway's exposed port if required by your service config

Render:
- Use a Web Service, not a Background Worker
- Start command: `python mcp_remote_server.py`
- Set `MCP_TRANSPORT=http`
- Set `MCP_HOST=0.0.0.0`
- Set `MCP_PORT=10000` or the port expected by your Render service settings

Horizon:
- Use `python mcp_remote_server.py` as the runtime command
- Set `MCP_TRANSPORT=http`
- Set `MCP_HOST=0.0.0.0`
- Set `MCP_PORT` to the port exposed by the Horizon deployment

Operational notes:
- `mcp_server.py` keeps Claude Desktop stdio mode working
- `mcp_remote_server.py` is the remote-friendly entrypoint
- `/health` can be used by load balancers and deployment health probes
- CORS is enabled for remote HTTP mode through `MCP_CORS_ALLOW_ORIGINS`
- Auth session state remains process-local and in-memory, just like the local MCP server

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
