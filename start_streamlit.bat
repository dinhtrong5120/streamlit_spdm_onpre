@echo off
cd /d "%~dp0"
echo ========================================
echo Starting SPDM Streamlit App
echo ========================================
echo.
echo IMPORTANT: This window will minimize automatically.
echo Do NOT click inside this window or the app will freeze!
echo.
echo If the app freezes, just press any key to continue.
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak > nul

REM Start streamlit and open browser (window will minimize)
start /min cmd /c "streamlit run app.py"

echo.
echo App is running! Check your browser at http://localhost:8501
echo To stop the app, close the minimized window.

