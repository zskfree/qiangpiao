@echo off
chcp 65001
echo ========================================
echo 🔍 抢票脚本环境检查
echo ========================================
echo.

echo 📁 检查文件结构...
if exist qiangpiao.py (
    echo ✅ qiangpiao.py - 主程序
) else (
    echo ❌ qiangpiao.py - 缺失
)

if exist config.py (
    echo ✅ config.py - 配置文件
) else (
    echo ❌ config.py - 缺失
)

if exist utils.py (
    echo ✅ utils.py - 辅助工具
) else (
    echo ❌ utils.py - 缺失
)

echo.
echo 🐍 测试Python环境...
D:/python/here312/python.exe --version 2>nul
if %errorlevel%==0 (
    echo ✅ Python环境正常
) else (
    echo ❌ Python环境异常
)

echo.
echo 📦 检查依赖包...
D:/python/here312/python.exe -c "import requests; print('✅ requests')" 2>nul
D:/python/here312/python.exe -c "import urllib3; print('✅ urllib3')" 2>nul

echo.
echo 🧪 语法检查...
D:/python/here312/python.exe -m py_compile qiangpiao.py 2>nul
if %errorlevel%==0 (
    echo ✅ qiangpiao.py 语法正确
) else (
    echo ❌ qiangpiao.py 语法错误
)

D:/python/here312/python.exe -m py_compile config.py 2>nul
if %errorlevel%==0 (
    echo ✅ config.py 语法正确
) else (
    echo ❌ config.py 语法错误
)

echo.
echo 📋 当前配置信息:
D:/python/here312/python.exe -c "from config import CONFIG; print(f'目标日期: {CONFIG[\"TARGET_DATE\"]}'); print(f'校区: {\"丽湖\" if CONFIG[\"XQ\"] == \"2\" else \"粤海\"}'); print(f'项目: {CONFIG[\"XMDM\"]}'); print(f'重试间隔: {CONFIG[\"RETRY_INTERVAL\"]}秒')" 2>nul

echo.
echo ========================================
echo ✅ 环境检查完成
echo ========================================
echo.
echo 💡 使用提示:
echo 1. 运行前请先更新Cookie: python utils.py cookie
echo 2. 启动抢票脚本: python qiangpiao.py
echo 3. 或直接双击 start.bat
echo.
pause
