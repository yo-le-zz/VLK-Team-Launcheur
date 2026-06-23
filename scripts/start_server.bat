@echo off
cd /d "%~dp0\.."
if not exist .env copy .env.example .env
pip install -r src/server/requirements.txt -q
uvicorn src.server.main:app --host 0.0.0.0 --port 8000 --reload
pause
