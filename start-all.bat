@echo off
title DermaScan AI - Auto Launcher
color 0B
echo ========================================================
echo        DERMASCAN AI - FULL SYSTEM AUTO-LAUNCHER
echo ========================================================
echo.

set SCRIPT_DIR=%~dp0

echo [1/3] Starting Local AI Backend (FastAPI + MobileNetV2)...
start "DermaScan AI - Backend (Port 8000)" cmd /k "cd /d "%SCRIPT_DIR%backend" && py -3.12 -m uvicorn app.main:app --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Live Public Tunnel (dermascan-parth-api)...
start "DermaScan AI - Live Tunnel" cmd /k "cd /d "%SCRIPT_DIR%" && npx localtunnel --port 8000 --subdomain dermascan-parth-api"

timeout /t 2 /nobreak >nul

echo [3/3] Starting Frontend Web Server (Vite React)...
start "DermaScan AI - Frontend" cmd /k "cd /d "%SCRIPT_DIR%frontend" && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo Launching DermaScan AI in browser...
start http://localhost:5173

echo.
echo ========================================================
echo       ALL SYSTEMS ARE RUNNING SUCCESSFULLY!
echo.
echo   * Local Frontend: http://localhost:5173
echo   * Local AI API:   http://localhost:8000
echo   * Live Tunnel:    https://dermascan-parth-api.loca.lt
echo   * Live Vercel:    https://dermascan-ai-eta.vercel.app
echo ========================================================
echo.
timeout /t 5 >nul
