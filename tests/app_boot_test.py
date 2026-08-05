"""Streamlit AppTest 启动冒烟测试：应用应能正常渲染，且空提交给出错误提示而非崩溃。"""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def main():
    root = Path(__file__).resolve().parent.parent
    at = AppTest.from_file(str(root / "app.py"), default_timeout=30)
    at.run()
    assert not at.exception, f"应用启动异常：{at.exception}"
    assert at.title[0].value == "🎓 MTI 翻译实践小助手 (Pro版)"
    assert len(at.sidebar.selectbox) >= 3, "侧边栏应有引擎/模型/目标语言选择框"

    # 空提交（无文件、无本地任务）应显示错误，不能崩溃
    at.button[0].click()
    at.run()
    assert not at.exception, f"空提交后异常：{at.exception}"
    assert at.error, "空提交应显示错误提示"
    print("AppTest 启动测试通过 ✅")


if __name__ == "__main__":
    main()
