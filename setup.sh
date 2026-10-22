#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -q -r agent-api/requirements.txt -r mcp-server/requirements.txt
(cd web-app && npm install)
[ -f .env ] || cp .env.example .env
echo "Setup complete. Run ./start.sh and open http://localhost:5173"
