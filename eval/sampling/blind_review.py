"""盲评抽样包生成。

结构（第一轮）：
- 40 段随机
- 10 段术语密集
- 10 段曾触发 repair/review（两臂任一 arm 有 findings 或初译≠终译）
- 10 段长句/高信息密度
- 10 段跨段上下文依赖明显

去重后最多 80 段；每段独立随机映射为 Candidate A / Candidate B
（评审者不知道哪个是 quality），映射关系写入本地 key 文件
（blind_review_key.csv，local-only，禁止入库）。
"""
from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mti_tool import models
from mti_tool.terminology import term_matches

MAX_PACKET = 80


def _context_dependent(segments: List[str], i: int) -> bool:
    """启发式：跨段上下文依赖（代词/连词开头、上一段句末未完结、引语延续）。"""
    if i <= 0:
        return False
    text = segments[i]
    head = text[:40].strip()
    if head.startswith(("But ", "And ", "He ", "She ", "It ", "They ", "This ",
                        "That ", "These ", "Those ", "His ", "Her ", "Its ",
                        "Their ", "Then ", "So ", "However", "Meanwhile",
                        '"', "“", "'", "‘")):
        return True
    prev = segments[i - 1].rstrip()
    if prev and prev[-1] not in ".!?…””":
        return True
    return False


def sample_packet(
    state_a: Dict[str, Any],
    state_b: Dict[str, Any],
    segments: List[str],
    glossary_entries: List[Dict[str, Any]],
    n_random: int = 40,
    n_term: int = 10,
    n_repair: int = 10,
    n_long: int = 10,
    n_ctx: int = 10,
    max_total: int = MAX_PACKET,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """返回 (packet_rows, key_rows)。packet 行含 source 与两臂译文（local-only）。"""
    rng = random.Random(seed)
    n = len(segments)
    if n == 0:
        return [], []

    # 类别索引
    def pair_arm(arm_state: Dict[str, Any], i: int) -> Dict[str, Any]:
        pairs = arm_state.get("pairs") or []
        return pairs[i] if 0 <= i < len(pairs) else {}

    flagged = [
        i for i in range(n)
        if any(fd.get("segment_index") == i for fd in
               (state_a.get("findings") or []) + (state_b.get("findings") or []))
        or any(
            pair_arm(st, i).get("initial_target")
            and pair_arm(st, i).get("initial_target") != pair_arm(st, i).get("target")
            for st in (state_a, state_b))
    ]
    entries = models.normalize_glossary(glossary_entries)

    def term_count(i: int) -> int:
        return sum(1 for e in entries
                   if e["status"] == "locked"
                   and term_matches(e["source"], segments[i]))

    term_dense = sorted(range(n), key=term_count, reverse=True)[:max(n_term, 0)]
    term_dense = [i for i in term_dense if term_count(i) >= 1]
    lengths = [(i, len(segments[i]) + 8 * segments[i].count(". ")) for i in range(n)]
    long_dense = [i for i, _ in sorted(lengths, key=lambda x: x[1], reverse=True)][:n_long]
    ctx = [i for i in range(n) if _context_dependent(segments, i)][:n_ctx]
    random_pick = rng.sample(range(n), min(n_random, n))

    categories = [
        ("random", random_pick),
        ("term_dense", term_dense),
        ("repair_review", flagged),
        ("long_dense", long_dense),
        ("context", ctx),
    ]
    chosen: List[Tuple[int, str]] = []
    seen = set()
    for cat, idxs in categories:
        for i in idxs:
            if len(chosen) >= max_total:
                break
            if i in seen:
                continue
            seen.add(i)
            chosen.append((i, cat))
    # 不足 80 时用随机池补齐
    for i in random_pick:
        if len(chosen) >= max_total:
            break
        if i in seen:
            continue
        seen.add(i)
        chosen.append((i, "random_fill"))

    packet_rows: List[Dict[str, Any]] = []
    key_rows: List[Dict[str, Any]] = []
    for pid, (i, cat) in enumerate(chosen, start=1):
        flip = rng.random() < 0.5
        pa, pb = pair_arm(state_a, i), pair_arm(state_b, i)
        tgt_a, tgt_b = pa.get("target", ""), pb.get("target", "")
        if flip:
            cand_a, cand_b = tgt_b, tgt_a
            a_is, b_is = "B", "A"
        else:
            cand_a, cand_b = tgt_a, tgt_b
            a_is, b_is = "A", "B"
        packet_rows.append({
            "packet_id": pid,
            "category": cat,
            "segment_id": i,
            "source": segments[i],
            "candidate_a": cand_a,
            "candidate_b": cand_b,
            # 评审填写（错误类型学）
            "a_terminology_error": "",
            "a_fidelity_error": "",
            "a_fluency_error": "",
            "a_omission": "",
            "a_comment": "",
            "b_terminology_error": "",
            "b_fidelity_error": "",
            "b_fluency_error": "",
            "b_omission": "",
            "b_comment": "",
            "overall_preference": "",
        })
        key_rows.append({"packet_id": pid, "segment_id": i, "category": cat,
                         "candidate_a_is_arm": a_is, "candidate_b_is_arm": b_is})
    return packet_rows, key_rows


def write_packet(packet_rows: List[Dict[str, Any]],
                 key_rows: List[Dict[str, Any]],
                 out_dir: Path,
                 prefix: str = "blind_review") -> Tuple[Path, Path]:
    """写入 CSV；key 文件与正文分离（key 严格 local-only）。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / f"{prefix}_packet.csv"
    key_path = out_dir / f"{prefix}_key.csv"
    if packet_rows:
        with packet_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(packet_rows[0].keys()))
            writer.writeheader()
            writer.writerows(packet_rows)
    if key_rows:
        with key_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(key_rows[0].keys()))
            writer.writeheader()
            writer.writerows(key_rows)
    return packet_path, key_path
