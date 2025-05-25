@echo off
echo 深圳大学体育场馆抢票脚本
echo ========================
echo.
echo 正在启动脚本...
echo.

REM 切换到脚本目录
cd /d %~dp0

REM 运行Python脚本
python qiangpiao.py

echo.
echo 脚本执行完毕，按任意键退出...
pause
