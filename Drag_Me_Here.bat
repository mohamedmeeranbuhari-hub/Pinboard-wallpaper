@echo off
echo ==============================================
echo  Aesthetic Bento Wallpaper Generator
echo ==============================================
echo.
python "%~dp0main.py" %*
echo.
echo Closing in 3 seconds...
timeout /t 3 >nul
