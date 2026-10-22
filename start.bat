@echo off
REM Windows launcher. Run setup first:  python -m venv .venv ^&^& .venv\Scripts\pip install -r agent-api\requirements.txt -r mcp-server\requirements.txt ^&^& cd web-app ^&^& npm install
cd /d %~dp0
set "PYTHONIOENCODING=utf-8"
if exist .env for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
start "MCP server" cmd /k "cd mcp-server && ..\.venv\Scripts\python server.py"
timeout /t 3 >nul
start "Agent API" cmd /k "cd agent-api && ..\.venv\Scripts\python main.py"
start "Web app" cmd /k "cd web-app && npm run dev"
echo Open http://localhost:5173
