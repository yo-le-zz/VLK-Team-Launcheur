#!/bin/bash
cd /home/ilan/Bureau/vlk-launcher
uv run uvicorn src.server.main:app --host 0.0.0.0 --port 8000 --reload