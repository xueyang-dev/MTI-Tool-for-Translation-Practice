"""统一 evaluation-report.json 写出。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_json_report(report: Dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "evaluation-report.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")
    return p
