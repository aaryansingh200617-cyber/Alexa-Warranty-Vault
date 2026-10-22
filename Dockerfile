FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY agent-api/requirements.txt ./agent-api/requirements.txt
COPY mcp-server/requirements.txt ./mcp-server/requirements.txt
RUN pip install --no-cache-dir -r agent-api/requirements.txt -r mcp-server/requirements.txt

COPY agent-api/ ./agent-api/
COPY mcp-server/ ./mcp-server/

COPY start-backend.sh ./start-backend.sh
RUN chmod +x ./start-backend.sh

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV PORT=8000

CMD ["./start-backend.sh"]
