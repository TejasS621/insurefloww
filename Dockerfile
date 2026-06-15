FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080

WORKDIR /app

COPY insureflow_mcp/requirements.txt /app/insureflow_mcp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/insureflow_mcp/requirements.txt

COPY insureflow_mcp /app/insureflow_mcp
COPY mcp_server.py /app/mcp_server.py
COPY mcp_remote_server.py /app/mcp_remote_server.py

RUN mkdir -p /app/storage/mcp_downloads

EXPOSE 8080

CMD ["python", "mcp_remote_server.py"]
