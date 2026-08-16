@echo off
chcp 65001 >nul
echo ==========================================
echo  Minitender.rf - Local Server Starter
echo ==========================================
echo.

set BACKEND_DIR=D:\Work\SaleManager\stroyzakup\backend
set FRONTEND_DIR=D:\Work\SaleManager\stroyzakup\frontend
set NODE=C:\Users\karpu\AppData\Local\Programs\kimi-desktop\resources\resources\runtime\node.exe
set PYTHONPATH=%BACKEND_DIR%\.venv\lib\python3.14\site-packages

REM Check if servers already running
curl -s -o nul -w "%%{http_code}" http://localhost:8000/api/ > %TEMP%\backend_check.txt 2>nul
set /p BACKEND_STATUS=<%TEMP%\backend_check.txt
curl -s -o nul -w "%%{http_code}" http://localhost:3000/ > %TEMP%\frontend_check.txt 2>nul
set /p FRONTEND_STATUS=<%TEMP%\frontend_check.txt

echo [1] Checking existing servers...

if "%BACKEND_STATUS%"=="401" (
    echo     Backend: already running on :8000
) else (
    echo     Backend: starting...
    start "Django Backend" cmd /k "cd /d %BACKEND_DIR% && set PYTHONPATH=%PYTHONPATH% && set DJANGO_SETTINGS_MODULE=config.settings.dev && python manage.py runserver 0.0.0.0:8000"
    timeout /t 4 /nobreak >nul
)

if "%FRONTEND_STATUS%"=="200" (
    echo     Frontend: already running on :3000
) else (
    echo     Frontend: starting...
    start "Next.js Frontend" cmd /k "cd /d %FRONTEND_DIR% && %NODE% node_modules\next\dist\bin\next start"
    timeout /t 5 /nobreak >nul
)

echo.
echo ==========================================
echo  All servers started!
echo ==========================================
echo.
echo  Site:     http://localhost:3000
echo  API:      http://localhost:8000/api/
echo  Admin:    http://localhost:8000/admin/
echo.
echo  Close this window to keep servers running.
echo  Close Django/Frontend terminal windows to stop.
echo.
pause
