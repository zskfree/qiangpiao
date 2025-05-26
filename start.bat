@echo off
chcp 65001 >nul
cls

echo.
echo   深大体育场馆预约 Web界面
echo   ==============================
echo.
echo   正在启动Web界面...
echo.

REM 切换到脚本目录
cd /d %~dp0

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo   错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查Flask是否安装
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo   正在安装Flask...
    pip install flask >nul 2>&1
    if errorlevel 1 (
        echo   Flask安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo   检查完成，启动Web服务器...
echo   服务地址: http://localhost:5000
echo.
echo   注意：关闭此窗口将停止Web服务
echo.

REM 直接运行Python脚本，不创建新窗口
python start_web.py

echo.
echo   Web服务已停止，按任意键退出...
pause >nul
