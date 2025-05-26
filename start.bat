@echo off
chcp 65001 >nul
cls

echo.
echo   SZU Sports Booking System - Web v1.0
echo   =====================================
echo.

REM 切换到脚本目录
cd /d %~dp0

REM 检查必要文件
if not exist "qiangpiao.py" (
    echo   [ERROR] Core file qiangpiao.py not found
    echo   Please ensure all files are complete
    pause
    exit /b 1
)

if not exist "web_app.py" (
    echo   [ERROR] web_app.py not found
    pause
    exit /b 1
)

REM 检查Python
echo   [INFO] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python not found
    echo   [TIP] Please install Python: https://python.org
    pause
    exit /b 1
)

REM 检查依赖
echo   [INFO] Checking dependencies...
python -c "import flask, requests" >nul 2>&1
if errorlevel 1 (
    echo   [INFO] Installing dependencies...
    pip install flask requests urllib3 >nul 2>&1
    if errorlevel 1 (
        echo   [ERROR] Failed to install dependencies
        echo   [TIP] Please check your network connection
        pause
        exit /b 1
    )
    echo   [SUCCESS] Dependencies installed
)

echo   [INFO] Starting web server...
echo   [INFO] Server address: http://localhost:5000
echo   [INFO] Browser will open automatically
echo.
echo   [WARNING] Closing this window will stop the service
echo.

REM 启动服务
python "start_web.py"

echo.
echo   [INFO] Web service stopped
pause >nul