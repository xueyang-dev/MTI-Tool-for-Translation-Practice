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

from transpraxis import models
from transpraxis.terminology import term_matches

MAX_PACKET = 80

PACKET_V2_FIELDS = [
    "packet_id", "category", "segment_id", "source",
    "candidate_a", "candidate_b",
    "candidate_a_terminology_error", "candidate_a_fidelity_error",
    "candidate_a_fluency_error", "candidate_a_omission",
    "candidate_b_terminology_error", "candidate_b_fidelity_error",
    "candidate_b_fluency_error", "candidate_b_omission",
    "overall_preference", "reviewer_note", "identical",
]


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


def sample_packet_v2(
    state_a: Dict[str, Any],
    state_b: Dict[str, Any],
    segments: List[str],
    glossary_entries: List[Dict[str, Any]],
    n_random: int = 40,
    n_term: int = 15,
    n_repair: int = 15,
    n_long: int = 10,
    max_total: int = MAX_PACKET,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """盲评包 v2：只比较 A vs B；优先保证 Candidate A != Candidate B。

    - informative = 两臂译文不同的段；类别池优先从 informative 中选取；
    - 有效差异不足时再从其余段补足到 max_total；
    - Candidate A/B 左右位置按 ~50/50 平衡分配（逐段随机映射）；
    - 返回 (packet_rows, key_rows)；key 与 packet 分离，local-only。
    """
    rng = random.Random(seed)
    n = len(segments)
    if n == 0:
        return [], []

    def pair(st: Dict[str, Any], i: int) -> Dict[str, Any]:
        pairs = st.get("pairs") or []
        return pairs[i] if 0 <= i < len(pairs) else {}

    def informative(i: int) -> bool:
        return (pair(state_a, i).get("target") or "") != \
            (pair(state_b, i).get("target") or "")

    informative_idx = [i for i in range(n) if informative(i)]
    identical_idx = [i for i in range(n) if not informative(i)]

    flagged = [
        i for i in range(n)
        if any(fd.get("segment_index") == i for fd in
               (state_a.get("findings") or []) + (state_b.get("findings") or []))
        or any(pair(st, i).get("initial_target")
               and pair(st, i).get("initial_target") != pair(st, i).get("target")
               for st in (state_a, state_b))
    ]
    entries = models.normalize_glossary(glossary_entries)

    def term_count(i: int) -> int:
        return sum(1 for e in entries
                   if e["status"] == "locked"
                   and term_matches(e["source"], segments[i]))

    term_dense = sorted(range(n), key=term_count, reverse=True)
    term_dense = [i for i in term_dense if term_count(i) >= 1]
    lengths = [(i, len(segments[i]) + 8 * segments[i].count(". ")) for i in range(n)]
    long_dense = [i for i, _ in
                  sorted(lengths, key=lambda x: x[1], reverse=True)]
    random_pool = list(range(n))
    rng.shuffle(random_pool)

    def pick(pool: List[int], limit: int) -> List[int]:
        out, seen = [], set()
        for i in pool:
            if len(out) >= limit:
                break
            if i in seen:
                continue
            seen.add(i)
            out.append(i)
        return out

    chosen: List[Tuple[int, str]] = []
    chosen_ids: set = set()

    def add(pool: List[int], cat: str, limit: int) -> None:
        for i in pool:
            if len(chosen) >= max_total:
                return
            if i in chosen_ids:
                continue
            chosen_ids.add(i)
            chosen.append((i, cat))

    # 类别优先从 informative 池取；不足时类别配额自动缩减（实际分布如实报告）
    add(pick([i for i in term_dense if i in set(informative_idx)], n_term),
        "term_dense", n_term)
    add(pick([i for i in flagged if i in set(informative_idx)], n_repair),
        "repair_review", n_repair)
    add(pick([i for i in long_dense if i in set(informative_idx)], n_long),
        "long_dense", n_long)
    add(pick([i for i in random_pool if i in set(informative_idx)],
             max_total - len(chosen)), "random", n_random)
    # 仍不足：从其余 informative 补
    add(pick([i for i in informative_idx if i not in chosen_ids],
             max_total - len(chosen)), "random_fill", max_total)
    # 仍不足：只能回退到 identical 对（数量会在报告里如实列出）
    add(pick([i for i in identical_idx if i not in chosen_ids],
             max_total - len(chosen)), "identical_fallback", max_total)

    # 左右位置平衡：~50/50 的 left-arm 分配
    left_arms = ["A"] * (len(chosen) // 2) + \
        ["B"] * (len(chosen) - len(chosen) // 2)
    rng.shuffle(left_arms)

    packet_rows: List[Dict[str, Any]] = []
    key_rows: List[Dict[str, Any]] = []
    for pid, ((i, cat), left_arm) in enumerate(
            zip(chosen, left_arms), start=1):
        tgt_a = pair(state_a, i).get("target", "")
        tgt_b = pair(state_b, i).get("target", "")
        if left_arm == "A":
            cand_a, cand_b, a_is, b_is = tgt_a, tgt_b, "A", "B"
        else:
            cand_a, cand_b, a_is, b_is = tgt_b, tgt_a, "B", "A"
        packet_rows.append({
            "packet_id": pid,
            "category": cat,
            "segment_id": i,
            "source": segments[i],
            "candidate_a": cand_a,
            "candidate_b": cand_b,
            "candidate_a_terminology_error": "",
            "candidate_a_fidelity_error": "",
            "candidate_a_fluency_error": "",
            "candidate_a_omission": "",
            "candidate_b_terminology_error": "",
            "candidate_b_fidelity_error": "",
            "candidate_b_fluency_error": "",
            "candidate_b_omission": "",
            "overall_preference": "",
            "reviewer_note": "",
            "identical": "0" if informative(i) else "1",
        })
        key_rows.append({"packet_id": pid, "segment_id": i, "category": cat,
                         "candidate_a_is_arm": a_is, "candidate_b_is_arm": b_is})
    return packet_rows, key_rows
