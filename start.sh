#!/usr/bin/env bash
# Starts the MCP server, agent API and web app. Run ./setup.sh once first.
set -e
cd "$(dirname "$0")"
[ -f .env ] && set -a && . ./.env && set +a
PY=.venv/bin/python
trap 'kill 0' EXIT
(cd mcp-server && ../$PY server.py) &
sleep 2
(cd agent-api && ../$PY main.py) &
(cd web-app && npm run dev) &
wait
