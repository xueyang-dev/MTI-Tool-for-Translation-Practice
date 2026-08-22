@echo off
:: 切换终端编码为 UTF-8，彻底解决中文乱码
chcp 65001 >nul

title TransPraxis / 译践 - 启动器
color 0b

echo ==========================================
echo       TransPraxis / 译践 正在启动...
echo ==========================================
echo.

:: 1. 切换到当前 bat 文件所在的目录，防止路径错误
cd /d "%~dp0"

:: 2. 自动创建虚拟环境并安装依赖（首次运行）
if not exist "venv\Scripts\activate.bat" (
    echo [系统] 未检测到虚拟环境，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败！请确认已安装 Python 3.10 或更高版本，并勾选 "Add Python to PATH"。
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo [系统] 首次运行，正在安装依赖，请耐心等待...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络后重试。
        pause
        exit /b 1
    )
) else (
    call venv\Scripts\activate.bat
)

:: 3. 启动 HTML GUI 包装器（自动打开浏览器；安装 pywebview 后为原生窗口）
echo [系统] 正在启动服务，请稍候...界面即将自动打开。
python gui.py

:: 4. 如果 Streamlit 意外退出，暂停窗口以便查看报错信息
pause
