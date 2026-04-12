@echo off
start "Frontend" cmd /k "cd /d %~dp0frontend && pnpm dev"
start "Backend" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\activate && python main.py"
