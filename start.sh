#!/usr/bin/env bash
# TransPraxis / 译践 —— macOS / Linux 一键启动（HTML GUI）
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "    TransPraxis / 译践 正在启动..."
echo "=========================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "[错误] 未找到 python3，请先安装 Python 3.10+。"
    read -r -p "按回车退出..." _
    exit 1
fi

if [ ! -x "venv/bin/python" ]; then
    echo "[系统] 未检测到虚拟环境，正在创建..."
    python3 -m venv venv
    echo "[系统] 首次运行，正在安装依赖，请耐心等待..."
    ./venv/bin/python -m pip install -r requirements.txt
fi

echo "[系统] 正在启动服务，界面将自动打开..."
./venv/bin/python gui.py

echo
read -r -p "服务已停止，按回车关闭窗口..." _
