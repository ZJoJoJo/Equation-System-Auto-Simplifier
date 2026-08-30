@echo off
chcp 65001 >nul
title 方程组自动化简软件（浏览器模式）
cd /d "%~dp0"
echo ========================================
echo   方程组自动化简软件（浏览器模式）
echo ========================================
echo.
echo 启动后将自动打开浏览器，访问 http://127.0.0.1:5000
echo 关闭此窗口即可停止服务。
echo.
python app.py --web
if errorlevel 1 (
    echo.
    echo 启动失败，请检查 Python 是否已安装。
    pause
)
