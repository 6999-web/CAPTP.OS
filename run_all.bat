@echo off
echo Starting FastAPI Backend...
start "CAPTP Backend" cmd /k "call ""%~dp0captp_env\Scripts\activate.bat"" && cd /d ""%~dp0backend"" && uvicorn main:app --reload --host 127.0.0.1 --port 8000"

echo Starting Vue Frontend...
start "CAPTP Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 127.0.0.1 --port 5173"

echo All services started! Close this window when done.
pause
