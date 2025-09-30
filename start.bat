@echo off
REM 检查是否安装了Python
where python >nul 2>nul
if %errorlevel% neq 0 (
echo 未找到Python，请先安装Python
pause
exit /b 1
)

REM 安装依赖
pip install -r requirements.txt

REM 启动应用程序
python watermarker.py

pause