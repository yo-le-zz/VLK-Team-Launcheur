#!/usr/bin/env bash
cd "$(dirname "$0")/.."
[ ! -f .env ] && cp .env.example .env
pip install -r src/server/requirements.txt -q
echo "Starting VLK Launcher API on port 8000..."
uvicorn src.server.main:app --host 0.0.0.0 --port 8000 --reload
