"""Style Profile 模块测试：预定义风格、结构化推荐降级、规则生成与版本 ID。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transpraxis import models
from transpraxis import style_profile


def test_profiles_are_predefined_and_closed():
    assert set(style_profile.STYLE_PROFILES) == {
        "academic", "technical", "professional", "literary",
        "legal", "publicity", "general"}
    for pid, meta in style_profile.STYLE_PROFILES.items():
        assert meta["name"] and meta["summary"] and meta["rules"]
        assert "params" in meta


def test_recommendation_normalization_clamps_unknown_style():
    rec = style_profile._normalize_style_recommendation({
        "recommended_style": "not-a-profile",
        "confidence": 5.0,
        "reasons": ["  a  ", "", "b"],
    })
    assert rec["recommended_style"] == "general"
    assert rec["confidence"] == 1.0
    assert rec["reasons"] == ["a", "b"]


def test_quick_profile_falls_back_deterministically():
    paragraphs = ["一段样本。" * 20] * 12

    def broken_llm(*args, **kwargs):
        raise RuntimeError("no llm")

    doc, rec, warnings = style_profile.quick_profile(
        paragraphs, "deepseek", "k", "m", call_llm=broken_llm)
    assert rec["recommended_style"] == "general"
    assert rec["confidence"] == 0.0
    assert any("快速画像失败" in w for w in warnings)
    assert doc == models.default_document_profile()


def test_quick_profile_empty_sample():
    doc, rec, warnings = style_profile.quick_profile(
        [], "deepseek", "k", "m")
    assert rec["recommended_style"] == "general"
    assert any("无可用的文本样本" in w for w in warnings)


def test_profile_to_rules_and_id():
    sel = {"selected": "academic", "adjustments": {"formality": 80}}
    rules = style_profile.profile_to_rules(sel)
    assert "保持正式、克制、客观" in rules
    assert "表达正式度：80/100" in rules
    assert style_profile.style_profile_id(sel) == \
        style_profile.style_profile_id(sel)
    assert style_profile.style_profile_id(sel) != \
        style_profile.style_profile_id({**sel, "selected": "technical"})


def test_core_write_profile_artifacts(tmp_path):
    import core
    old_dir = core.OUTPUT_DIR
    core.OUTPUT_DIR = tmp_path
    job_id = "sp000000000000001"
    sel = {"selected": "academic", "source": "accepted", "adjustments": {}}
    try:
        pid = core.write_profile_artifacts(
            job_id, {"domain": "传播学", "confidence": 0.8}, sel)
        assert pid
        root = core.job_dir(job_id)
        assert (root / "document_profile.json").exists()
        style_artifact = (root / "style_profile.json").read_text(encoding="utf-8")
        assert f'"style_profile_id": "{pid}"' in style_artifact
        assert "academic" in style_artifact
    finally:
        core.OUTPUT_DIR = old_dir


def main():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_profiles_are_predefined_and_closed()
        test_recommendation_normalization_clamps_unknown_style()
        test_quick_profile_falls_back_deterministically()
        test_quick_profile_empty_sample()
        test_profile_to_rules_and_id()
        test_core_write_profile_artifacts(Path(tmp))
    print("Style Profile 测试通过 ✅")


if __name__ == "__main__":
    main()
