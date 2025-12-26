@echo off
chcp 65001 >nul
echo ================================
echo Modbus 设备管理工具 v2.0
echo ================================
echo.
echo 正在启动程序...
echo.

cd /d "%~dp0"
poetry run python src/pymodbus_gui/run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 程序异常退出，错误代码: %ERRORLEVEL%
    echo 按任意键关闭...
    pause >nul
)
