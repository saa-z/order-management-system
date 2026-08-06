@echo off
title San Giorgio - OMS
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"

cd /d "%ROOT%"
start "SanGiorgio-Serveur" /min "%PY%" -m uvicorn main:app --host 0.0.0.0 --port 8000

timeout /t 3 /nobreak > nul

cd /d "%ROOT%frontend"
"%PY%" app.py

taskkill /fi "WINDOWTITLE eq SanGiorgio-Serveur" /f > nul 2>&1
