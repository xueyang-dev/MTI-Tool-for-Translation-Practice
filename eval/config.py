"""评测配置加载与校验。

配置为 JSON 文件（真实运行配置放在 eval/results/ 下，local-only，不入库）。
示例见 eval/config.example.json。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "code": {
        "baseline_ref": "HEAD",
    },
    "corpus": {
        # 仅在本地配置中填写任务 ID；发布配置不包含本地任务。
        "job_id": "",
        "subset": [0, 0],
    },
    "glossary": "",
    "tm_seed": "outputs/translation_memory.json",
    "run": {
        "provider": "DeepSeek",
        "model": "deepseek-v4-flash",
        "target_lang": "简体中文",
        "translation_theory": "目的论 (Skopos Theory)",
        "style_rules": "保持学术书面语；专有名词、作者姓名、机构名、引用标注、URL 等保留原文；"
                       "标点遵循目标语言规范。",
        "enable_review": True,
        "enable_annotate": False,
        "enable_report": False,
        # 各运行臂共用同一批参数；temperature 由代码固定。
    },
    "arms": ["A", "B", "C", "D"],
    "seed": 42,
    "out_dir": "",
}


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"配置文件不存在：{p}")
        user = json.loads(p.read_text(encoding="utf-8"))
        _deep_update(cfg, user)
    _validate(cfg)
    return cfg


def _deep_update(base: Dict[str, Any], patch: Dict[str, Any]) -> None:
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v


def _validate(cfg: Dict[str, Any]) -> None:
    arms = cfg["arms"]
    for arm in arms:
        if arm not in ("A", "B", "C", "D"):
            raise ValueError(f"非法 arm：{arm}（只能 A/B/C/D）")
    subset = cfg["corpus"]["subset"]
    if len(subset) != 2 or subset[0] < 0 or subset[1] < 0 or subset[1] < subset[0]:
        raise ValueError(f"corpus.subset 必须为 [start, end]（end>=start，0 表示无意义）：{subset}")
    if cfg["corpus"]["job_id"]:
        # 真实语料必须在 outputs/ 中存在（读取时才最终校验）
        pass


def describe_run_matrix(arms: List[str]) -> str:
    """A/B/C/D 四臂实验矩阵说明（Governance × Reviewed TM）。"""
    rows = {
        "A": ("baseline", "无", "无"),
        "B": ("current code + quality mode", "有", "无"),
        "C": ("baseline", "无", "有"),
        "D": ("current code + quality mode", "有", "有"),
    }
    lines = ["Run  Governance  ReviewedTM"]
    for arm in arms:
        desc, gov, tm = rows[arm]
        lines.append(f"{arm}  {gov:>3}  {tm:>9}  ({desc})")
    return "\n".join(lines)


def resolve_glossary_entries(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    path = cfg.get("glossary")
    if not path:
        return []
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"术语表文件不存在：{p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "entries" in data:
        return data["entries"]
    if isinstance(data, list):
        return data
    raise ValueError(f"术语表文件格式错误（需要 entries 列表或条目数组）：{path}")
