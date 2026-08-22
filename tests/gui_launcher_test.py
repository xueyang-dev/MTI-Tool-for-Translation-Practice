"""HTML GUI 启动器（gui.py）纯逻辑测试：不真正启动服务、不打开窗口。"""
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gui


def test_brand_title():
    assert gui.APP_TITLE == "TransPraxis / 译践"
    print("  ✓ 桌面窗口品牌标题")


def test_server_args():
    args = gui.server_args(8501, lan=False)
    assert args[:3] == ["-m", "streamlit", "run"]
    assert Path(args[3]) == gui.ROOT / "app.py"
    assert "--server.headless" in args and "true" in args
    assert "--server.port" in args and "8501" in args
    assert args[args.index("--theme.primaryColor") + 1] == "#1267e8"
    assert args[args.index("--theme.textColor") + 1] == "#131c2e"
    assert "--server.address" not in args, "非 lan 模式不应绑定 0.0.0.0"

    lan_args = gui.server_args(9000, lan=True)
    assert "--server.address" in lan_args
    assert lan_args[lan_args.index("--server.address") + 1] == "0.0.0.0"
    print("  ✓ server_args（headless/端口/lan 绑定）")


def test_pick_port():
    # 占用一个端口后，pick_port 应顺延到下一个可用端口
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        taken = s.getsockname()[1]
        picked = gui.pick_port(taken)
        assert picked != taken, "被占用端口应被跳过"
        assert taken < picked < taken + 20
    print("  ✓ pick_port（端口顺延）")


def test_url_for():
    assert gui.url_for(8501, lan=False) == "http://127.0.0.1:8501"
    lan_url = gui.url_for(9000, lan=True)
    assert lan_url == f"http://{gui.lan_ip()}:9000"
    print("  ✓ url_for（本机 / 局域网）")


def test_lan_ip_is_ipv4():
    ip = gui.lan_ip()
    parts = ip.split(".")
    assert len(parts) == 4 and all(p.isdigit() for p in parts)
    print("  ✓ lan_ip 返回 IPv4 地址")


def main():
    test_brand_title()
    test_server_args()
    test_pick_port()
    test_url_for()
    test_lan_ip_is_ipv4()
    print("GUI 启动器逻辑测试通过 ✅")


if __name__ == "__main__":
    main()
