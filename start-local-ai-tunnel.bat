@echo off
title DermaScan AI - Local Server + Live Vercel Tunnel
color 0A

echo =====================================================================
echo           DERMASCAN AI - LOCAL AI ENGINE + VERCEL TUNNEL
echo =====================================================================
echo.
echo [*] Starting FastAPI Backend on port 8000 with MobileNetV2 AI Model...
echo.

cd /d "%~dp0\backend"
start "DermaScan AI Backend (Port 8000)" cmd /k "py -3.12 -m uvicorn app.main:app --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [*] Starting Cloudflare HTTPS Live Tunnel to Vercel...
echo.
cd /d "%~dp0"
start "DermaScan AI Live Cloudflare Tunnel" cmd /k "cloudflared.exe tunnel --url http://localhost:8000"

echo.
echo =====================================================================
echo  [+] Local Backend is running on: http://localhost:8000
echo  [+] Look at the "DermaScan AI Live Cloudflare Tunnel" window.
echo  [+] Find and copy your HTTPS URL:
echo      Example: https://xxxx-xxxx.trycloudflare.com
echo.
echo  [+] Put that URL in Vercel Environment Variables:
echo      VITE_API_URL = https://xxxx-xxxx.trycloudflare.com/api
echo      VITE_API_BASE_URL = https://xxxx-xxxx.trycloudflare.com/api
echo =====================================================================
echo.
pause
