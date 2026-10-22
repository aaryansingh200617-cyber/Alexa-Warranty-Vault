#!/bin/sh
set -e

echo "Starting MCP Server on port 8765..."
(cd mcp-server && python server.py) &
sleep 2

echo "Starting Agent API on port ${PORT:-8000}..."
cd agent-api && python main.py
