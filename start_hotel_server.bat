@echo off
title The Grand Horizon Hotel Management System - 24/7 Server
cd /d "%~dp0"
echo ===================================================================
echo  THE GRAND HORIZON LUXURY HOTEL & RESORT - MANAGEMENT SYSTEM
echo  Server is starting on: http://127.0.0.1:5000
echo ===================================================================
call .\venv\Scripts\activate.bat
python run.py
pause

