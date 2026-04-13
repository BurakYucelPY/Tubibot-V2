@echo off
echo Starting Tubibot V2 Development Environment...

start "Frontend" cmd /k "cd /d "%~dp0frontend" && pnpm dev"

start "Backend" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate && cd backend && uvicorn api:app --reload --host 0.0.0.0 --port 8000"

echo Both servers are starting up!
