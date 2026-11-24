
@echo off
title AI COLLISION WARNING SYSTEM

cd /d "%~dp0"

echo ==========================================
echo     AI COLLISION WARNING SYSTEM
echo ==========================================
echo.
echo Dang khoi dong he thong...

if not exist ".venv\Scripts\python.exe" (
    echo Khong tim thay moi truong Python .venv!
    echo Vui long cai dat moi truong truoc.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run "gui\dashboard.py"

pause
