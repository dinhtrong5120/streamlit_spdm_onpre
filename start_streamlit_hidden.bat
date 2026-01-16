@echo off
cd /d "%~dp0"
echo ========================================
echo Starting SPDM Streamlit App
echo ========================================
echo.
echo The terminal will run in the background (minimized).
echo Your browser will open automatically.
echo.
echo To STOP the app, press Ctrl+C in the PowerShell window
echo or close the minimized PowerShell window.
echo.

REM Use PowerShell to run streamlit in a minimized window
powershell -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd ''%~dp0''; streamlit run app.py' -WindowStyle Minimized"

echo.
echo App started! Check your browser at http://localhost:8501
echo.
pause

