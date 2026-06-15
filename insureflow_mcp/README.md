# InsureFlow MCP

`insureflow_mcp/` contains the complete InsureFlow MCP package.

This MCP is intentionally thin:
- validates MCP tool inputs
- calls the existing InsureFlow main backend
- normalizes backend responses into MCP-friendly results
- applies retries, timeouts, and structured error handling

It does not implement quote generation, underwriting, payment processing, or any other backend business logic.

## Supported Tools

- `generate_quote`
- `select_quote`
- `initiate_payment`
- `get_payment_status`

These are the only tools kept because they map directly to public customer-flow backend routes without requiring a login-only session inside the MCP.

## Package Layout

```text
insureflow_mcp/
  clients/
  core/
  schemas/
  tests/
  tools/
  .env.example
  README.md
  requirements.txt
```

## Install

```powershell
pip install -r insureflow_mcp/requirements.txt
```

## Environment

Copy the example file and update values if needed:

```powershell
Copy-Item insureflow_mcp/.env.example .env
```

Main variables:
- `MAIN_BACKEND_URL=http://localhost:8000/api/v1`
- `MCP_TRANSPORT=stdio`
- `MCP_HOST=0.0.0.0`
- `MCP_PORT=8080`
- `MCP_HTTP_PATH=/mcp`
- `MCP_HEALTH_PATH=/health`
- `MCP_API_KEY=`

## Run Locally

Local stdio MCP for Claude Desktop:

```powershell
python mcp_server.py
```

Remote HTTP MCP:

```powershell
$env:MCP_TRANSPORT="http"
python mcp_remote_server.py
```

Health check:

```text
http://localhost:8080/health
```

Remote MCP endpoint:

```text
http://localhost:8080/mcp
```

## Claude Desktop

Example local stdio config:

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

## Remote Deployment Notes

- `mcp_remote_server.py` keeps remote HTTP transport support.
- `horizon_server.py:server` remains the Horizon export target.
- `/health` stays public.
- If `MCP_API_KEY` is set, remote MCP requests must send `X-MCP-API-Key`.

## Tests

```powershell
python -m pytest insureflow_mcp/tests
```
