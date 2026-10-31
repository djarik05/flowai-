@echo off
title GestureFlow AI Launcher
echo ============================================================
echo           Starting GestureFlow AI Unified Launcher
echo ============================================================
if exist "backend\.venv\Scripts\python.exe" (
    backend\.venv\Scripts\python.exe run.py %*
) else (
    python run.py %*
)
