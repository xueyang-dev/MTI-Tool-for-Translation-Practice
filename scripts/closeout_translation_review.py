"""Close the real ec100 translation review without rewriting its history.

The script preserves every stored initial translation, backs up the complete
pre-review state, records a disposition for each open actionable finding, and
keeps system alignment repairs permanently ineligible for thesis case use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from mti_tool import academic_evidence, academic_writer, delivery, state_migration


JOB_ID = "ec100d8686d3891e"
RUN_ID = "translation-review-closeout-v1"
ACTOR = "system_academic_review"


TARGET_REPAIRS: dict[int, str] = {
    1: "泽夫·拉兹",
    4: "希伯来文译者：萨拉·马吉尼",
    5: "编辑：埃文·戈登",
    7: "献给祖母萨拉和祖父雅科夫",
    14: "牢狱大暴动",
    56: "“接下来就靠你自己了。”我通过只有我和他能听见的无线电频率告诉他。",
    57: "他左翼尖端的红灯慢慢从我眼前飘远，一切正如应有的那样。真是个飞行员。太棒了。",
    59: "八千英尺，三百二十节，航向285度，地平线稳定。这该死的“神秘”式飞机的地平仪。就连“马吉斯特”教练机的人工地平仪都比它强。",
    80: "然而，“库尔纳斯”那具精良的球形人工地平仪显示的却完全是另一回事。",
    81: "飞机正平缓左转，机头恰好位于地平线上。",
    82: "我陷入了空间定向障碍，沙乌尔正坐在后座舱里。",
    83: "“我来接管！”他立即对我说。",
    93: "刹那间，一切都各就其位，彼此对准。",
    101: "战争中，人可以死。",
    103: "我们在基利波山对面长大，那座山仿佛就是世界的尽头。我们看着努里斯、马扎尔和扎林几个村庄的废墟渐渐消失，努里特和伊兹雷尔村取而代之。",
    119: "礼赞困惑，谴责笃定",
    139: "那时，父亲还没有盖房子，仍在修理机器。即便当时，我想自己已经隐约意识到：他会做一些我永远也做不到的事。多年后，我请他教我焊接。他仍用一贯的口吻答道：“学那个干什么？”又一次避开了我伸向他的手。",
    140: "露丝端来咖啡，问三岁半的我格瓦那边怎么样。有人走进来，拍了拍阿扎里亚的肩膀，问：“帕尔马赫部队究竟为什么解散？”“去问本-古里安，或者塔本金。”阿扎里亚面无笑意地答道。那一刻，贝特哈希塔的小房间里掠过一阵悲凉。屋内挂着古特曼画的几朵白银莲花，却没有收音机或电话；和别处一样，门也根本无须上锁。",
    141: "“塔本金是谁？”我问。当天晚上晚些时候，祖父——父亲的父亲——回答了这个问题，却不愿谈本-古里安。1958年春，以色列建国十周年庆典之后，他告诉我，自己曾对劳工锡安主义奠基人之一贝尔·卡茨内尔森说：“你要那个本-古里安干什么？”",
    142: "爸爸发动吉普车前，妈妈对他说：“现在你该知道我的咖啡有多好了。”爸爸笑着答道：“刚才那是菊苣。”“什么是菊苣？”我问。妈妈讲起物资紧缩时期，以及时任配给部长多夫·约瑟夫。回程向西没开多远，我看见妈妈把左手放在",
    145: "达扬在独立战争中阵亡的哥哥佐里克命名的。达扬以刀锋般锐利的目光直视父亲，和他握了握手，又提起在耶路撒冷战役中阵亡的莫塔。",
    151: "我们十五岁。时值深秋。当时秋水仙正在开放，海葱的花期已经过去。",
    152: "晚饭后，我再次向西穿过塞德旱谷，去见伊里特。小学毕业前我们一起读书时，我就爱上了她。",
    155: "我们手牵着手，沿大家称作“斜坡”的坡道向下走，寻找枣子。",
    156: "凡是在那条旱谷一侧岸边长大的人，都熟悉那里的玄武岩，以及结着橙色果实的多刺枣树。",
    170: "我们当时十九岁。正值夏天，或是夏末。金鱼草开着白花，茴香开着黄花。队伍中一个戴针织基帕帽的人告诉我们，茴香叶可以吃；尝起来果然不错——有茴芹味。",
    201: "我的电话响了。",
    209: "牢狱大暴动",
    216: "归途中，阿莫斯唱起《为我漂泊的民族建立一个国家》《加利利的特尔海》和《星期五晚上我总是没衣服穿》。女孩们跟着他唱，有几个男孩也加入了。",
    233: "路上，阿莫斯说海法有两部电影可看——皇宫影院放《热情似火》，多米诺影院放《牢狱大暴动》。女孩们想去皇宫，我们想去多米诺。投票结果打成平手——十一个女孩对十一个男孩。他低声念叨：“皇宫，皇宫。”阿莫斯说，既然平票，就由他决定：去多米诺。有人说：“玛丽莲·梦露。”阿莫斯回答：“要是碧姬·芭铎还差不多……”诺姆又加了一句：“或者罗妮·霍夫纳。”但他坐在卡车第二排最那头，她没有听见。",
    234: "接着她说：“阿莫斯，给我够买票的钱，再把我们放在皇宫影院。怎么样？我们已经不是小孩子了。”阿莫斯看着她，面无笑意地说：“不行。绝对不行。所有人都得在一起。”茨维卡总和阿米一起打篮球、挤羊奶，这时却说要改投皇宫一票……说完笑了。阿莫斯说，投票既已结束，谁都不能改主意，否则永远没完。于是我们去了多米诺影院。",
    235: "他喜欢茨维卡。茨维卡教他，九十九后面是一百。他呼吸困难时，茨维卡从不笑他；诺姆把他背回岸边时，茨维卡当然也没有笑。有时候，茨维卡甚至会陪他打篮球，尽管他的水平比不上茨维卡，也比不上阿米，更不用说乌兹和阿姆农了。",
    236: "他负责照料儿童动物园里的兔子。兔子生病、耳朵长疮时，茨维卡给了他一种特制药膏，还帮他涂上。随后，茨维卡从口袋里掏出几颗杏仁递给他。他吃着杏仁说：“茨维卡，等我们长大了，就和丹尼尔一起种杏树。”茨维卡放声大笑，说：",
    239: "达莉亚走出多米诺影院时，一张纸从她一直拿着的书里滑落，他捡了起来。那不是书页，而是一张手写的纸：",
}


REPAIR_NOTES: dict[int, str] = {
    4: "将版权页译者姓名转写为中文，清除残留英文。",
    5: "将编辑姓名转写为中文，清除残留英文。",
    7: "调整题献语中文语序并统一姓名转写。",
    14: "将同名章节标题统一为已核验影片译名《牢狱大暴动》。",
    56: "按单飞放手语境改为自然中文表达。",
    57: "恢复缓慢飘离的动态并收紧叙事评价。",
    59: "补足航向单位并统一机型和仪表术语。",
    80: "修正人工地平仪的搭配并统一机型译名。",
    81: "将不自然的转弯搭配改为飞行常用表达。",
    82: "保留术语“空间定向障碍”，改正句法并统一人名。",
    83: "明确即时接管动作和对话表达。",
    103: "统一地名音译，移除无必要的英文括注。",
    119: "将标题改为对称、凝练的中文结构。",
    139: "保留原文手势隐喻，同时改善中文句法与叙事节奏。",
    140: "统一专名译法并改善长句衔接；不采纳机械回填英文的建议。",
    141: "统一专名和政治术语译法；不采纳机械保留英文的建议。",
    144: "清除模型序列化外壳，并按0144/0145的真实跨段句法重新切分。",
    155: "保留带引号的地点称呼，删除“斜坡/山坡”重复。",
    156: "用“旱谷”传达wadi的地理意义并改善中文句法。",
    170: "明确两种植物及其对应颜色，消除“交织”的额外意象。",
    216: "补回遗漏的合唱句；歌曲标题采用中文译名，不机械回填英文。",
    233: "采用可核验片名《牢狱大暴动》，恢复明确主语并改善叙事衔接。",
    234: "恢复give me enough for the tickets的论元结构。",
    235: "统一人物姓名译法并消除代词关系歧义。",
    239: "移除相邻段重复译文，恢复本段完全漏译的手写纸页信息。",
}


SYSTEM_FLAGS: dict[int, list[dict[str, str]]] = {
    1: [{
        "type": "system_alignment_repair",
        "reason": "历史终译把作者名ZE’EV RAZ误写成书名语义。",
    }],
    14: [{
        "type": "system_terminology_consistency_repair",
        "reason": "章节标题与正文中同名影片的已核验译名不一致；统一为《牢狱大暴动》。",
    }],
    93: [{
        "type": "system_alignment_repair",
        "reason": "历史初译和终译均复制0092内容，与0093源文不对应。",
    }],
    101: [{
        "type": "system_alignment_repair",
        "reason": "历史初译和终译均复制0100内容，与0101源文不对应。",
    }],
    142: [{
        "type": "system_boundary_repair",
        "reason": "历史终译吞入0143内容；按PDF跨页边界恢复后仍不得作为真实修订案例。",
    }],
    144: [{
        "type": "serialized_model_output_repair",
        "reason": "历史译文带JSON代码围栏且源句跨0144/0145分段。",
    }, {
        "type": "system_boundary_repair",
        "reason": "0144/0145的源句跨段存储，终译按相同边界重新切分。",
    }],
    145: [{
        "type": "system_boundary_repair",
        "reason": "0144/0145的源句跨段存储，终译按相同边界重新切分。",
    }],
    209: [{
        "type": "system_alignment_repair",
        "reason": "历史初译来自0208，历史终译未翻译章节标题。",
    }],
    201: [{
        "type": "system_alignment_repair",
        "reason": "历史初译和终译均复制0200内容，与0201源文不对应。",
    }],
    236: [{
        "type": "system_alignment_repair",
        "reason": "历史初译和终译均复制0235内容，与0236源文不对应。",
    }],
    239: [{
        "type": "system_alignment_repair",
        "reason": "历史初译和终译均复制0238内容，与0239源文不对应。",
    }],
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clean_0144(raw: str) -> str:
    text = re.sub(r"^```json\s*\[\s*\"", "", raw.strip())
    text = re.sub(r"\",\s*\]\s*```$", "", text)
    old_tail = "爸爸走近他，告诉他，他给自己的第二个儿子取名为"
    if not text.endswith(old_tail):
        raise RuntimeError("0144 serialized target shape changed; refusing blind repair")
    return text[:-len(old_tail)] + "爸爸走近达扬，告诉他，自己的次子是以"


def _add_action(state: dict[str, Any], finding_id: str, action: str,
                note: str, timestamp: str) -> None:
    state.setdefault("system_actions", []).append({
        "finding_id": finding_id,
        "action": action,
        "note": note,
        "timestamp": timestamp,
        "actor": ACTOR,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", default=JOB_ID)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    state_path = Path("outputs") / args.job_id / "state.json"
    out_dir = Path(args.out_dir)
    backup_path = out_dir / "translation-state-before-review.json"
    reviewed_state_path = out_dir / "translation-state-after-review.json"
    audit_path = out_dir / "translation-review-audit.json"
    report_path = out_dir / "translation-review-report.md"
    manifest_path = out_dir / "translation-review-run-manifest.json"
    state = _load(state_path)

    if state.get("closeout_translation_review", {}).get("run_id") == RUN_ID:
        required = (backup_path, audit_path, report_path, manifest_path)
        if not all(path.is_file() for path in required):
            parser.error("state is marked complete but closeout artifacts are missing")
        misplaced = [
            action for action in state.get("human_actions") or []
            if action.get("actor") == ACTOR
        ]
        if misplaced:
            state["human_actions"] = [
                action for action in state.get("human_actions") or []
                if action.get("actor") != ACTOR
            ]
            existing = {
                json.dumps(action, ensure_ascii=False, sort_keys=True)
                for action in state.get("system_actions") or []
            }
            for action in misplaced:
                identity = json.dumps(action, ensure_ascii=False, sort_keys=True)
                if identity not in existing:
                    state.setdefault("system_actions", []).append(action)
                    existing.add(identity)
            state["closeout_translation_review"]["system_actions_separated"] = True
            core.save_job_state(args.job_id, state)
            after_hash = _sha256(state_path)
            audit = _load(audit_path)
            audit["post_review_state_sha256"] = after_hash
            audit["system_actions_separated_from_human_actions"] = True
            audit["content_hash"] = academic_evidence.stable_hash(
                {k: v for k, v in audit.items() if k != "content_hash"})
            _write(audit_path, audit)
            manifest = _load(manifest_path)
            manifest["state_sha256_after"] = after_hash
            _write(manifest_path, manifest)
        if not reviewed_state_path.is_file():
            shutil.copyfile(state_path, reviewed_state_path)
        supplemental_targets = {index: TARGET_REPAIRS[index]
                                for index in (1, 14, 93, 101, 201)}
        applied = []
        for index, target in supplemental_targets.items():
            pair = state["pairs"][index]
            if pair.get("target") != target:
                pair["target"] = target
                pair["from_tm"] = False
                pair["reviewed"] = True
                pair["integrity_flags"] = SYSTEM_FLAGS[index]
                _add_action(
                    state, f"segment:{index}", "system_alignment_fixed",
                    SYSTEM_FLAGS[index][0]["reason"],
                    datetime.now(timezone.utc).isoformat(timespec="seconds"))
                applied.append(index)
        if applied:
            state["closeout_translation_review"]["supplemental_alignment_repairs"] = applied
            state["closeout_translation_review"]["translation_targets_changed"] = sorted(set(
                state["closeout_translation_review"].get(
                    "translation_targets_changed") or []) | set(applied))
            state["closeout_translation_review"]["system_repair_segments"] = sorted(set(
                state["closeout_translation_review"].get(
                    "system_repair_segments") or []) | set(applied))
            core.save_job_state(args.job_id, state)
            shutil.copyfile(state_path, reviewed_state_path)
            after_hash = _sha256(state_path)
            audit = _load(audit_path)
            audit["post_review_state_sha256"] = after_hash
            audit["supplemental_alignment_repairs"] = applied
            audit["changed_segment_indexes"] = sorted(set(
                audit.get("changed_segment_indexes") or []) | set(applied))
            audit["system_repair_segments"] = sorted(set(
                audit.get("system_repair_segments") or []) | set(applied))
            audit["content_hash"] = academic_evidence.stable_hash(
                {k: v for k, v in audit.items() if k != "content_hash"})
            _write(audit_path, audit)
            manifest = _load(manifest_path)
            manifest["state_sha256_after"] = after_hash
            _write(manifest_path, manifest)
        print(out_dir)
        return 0

    original_actionables = [
        f for f in state.get("findings") or []
        if f.get("severity") == "actionable" and not f.get("resolved")
    ]
    if len(original_actionables) != 32:
        parser.error(f"expected 32 open actionable findings, found {len(original_actionables)}")
    unreviewed_before = [
        i for i, pair in enumerate(state.get("pairs") or [])
        if not pair.get("reviewed")
    ]
    if unreviewed_before != [4, 5, 7, 139, 142, 144, 152, 209, 215]:
        parser.error(f"unexpected unreviewed baseline: {unreviewed_before}")

    out_dir.mkdir(parents=True, exist_ok=True)
    if backup_path.exists():
        parser.error("backup already exists while state is not marked complete")
    shutil.copyfile(state_path, backup_path)
    before_hash = _sha256(backup_path)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    targets = dict(TARGET_REPAIRS)
    targets[144] = _clean_0144(state["pairs"][144]["target"])
    changed: list[int] = []
    for index, target in sorted(targets.items()):
        pair = state["pairs"][index]
        if pair.get("target") != target:
            pair["target"] = target
            pair["from_tm"] = False
            changed.append(index)
        pair["reviewed"] = True
        if index in SYSTEM_FLAGS:
            pair["integrity_flags"] = SYSTEM_FLAGS[index]

    # 0145 and 0236 are system resegmentation repairs discovered during the
    # full-source audit, even though the original finding set did not flag them.
    for index in SYSTEM_FLAGS:
        state["pairs"][index]["integrity_flags"] = SYSTEM_FLAGS[index]
        state["pairs"][index]["reviewed"] = True
        state["pairs"][index]["from_tm"] = False

    dispositions: list[dict[str, Any]] = []
    for finding in original_actionables:
        index = int(finding["segment_index"])
        fid = delivery.finding_id(finding)
        if index == 171:
            action = "finding_rejected"
            note = ("驳回误报：sent some of us to the hospital本身包含结果关系；"
                    "译文“因此”未添加原文不存在的因果，原译可保留。")
        elif index == 215:
            action = "finding_rejected"
            note = ("驳回误报：中文文学译文采用稳定音译/意译，无需机械回填Atlit、"
                    "Rabbits Hideaway和Chair Hill。")
        elif index == 152:
            action = "finding_reassigned"
            note = "finding引用秋水仙/海葱，但0152源文与终译均无该内容；问题实际属于0151。"
        else:
            action = "system_fixed"
            note = REPAIR_NOTES[index]
        finding["resolved"] = True
        finding["resolution"] = {
            "action": action,
            "note": note,
            "timestamp": timestamp,
            "actor": ACTOR,
        }
        _add_action(state, fid, action, note, timestamp)
        dispositions.append({
            "finding_id": fid,
            "segment_index": index,
            "disposition": action,
            "note": note,
        })

    # Correct the misassigned 0152 finding without editing its historical record.
    for index, reason, note in (
        (151,
         "系统复核确认原文no longer the squills表示海葱花期已经过去，原译关系不清。",
         "将0152错挂finding所指问题转挂到真实段落0151并完成修复。"),
        (152,
         "系统复核发现Wadi Seder与Irit仍残留英文，且后句中文关系生硬。",
         "统一地名、人名译法并重组后句。"),
    ):
        finding = {
            "segment_index": index,
            "severity": "actionable",
            "type": "system_academic_review",
            "reason": reason,
            "resolved": True,
            "resolution": {
                "action": "system_fixed",
                "note": note,
                "timestamp": timestamp,
                "actor": ACTOR,
            },
        }
        finding["id"] = delivery.finding_id(finding)
        state.setdefault("findings", []).append(finding)
        _add_action(state, finding["id"], "system_fixed", note, timestamp)

    for index in sorted(SYSTEM_FLAGS):
        note = SYSTEM_FLAGS[index][0]["reason"]
        _add_action(state, f"segment:{index}", "system_alignment_fixed", note, timestamp)

    # Mark every formerly unreviewed segment reviewed after the focused source audit.
    for index in unreviewed_before:
        state["pairs"][index]["reviewed"] = True
        state["pairs"][index]["from_tm"] = False

    active = [f for f in state.get("findings") or [] if not f.get("resolved")]
    counts = Counter(str(f.get("severity") or "unknown") for f in active)
    recorded = Counter(str(f.get("severity") or "unknown")
                       for f in state.get("findings") or [])
    stats = state.setdefault("review_stats", {})
    stats.update({
        "reviewed_segments": sum(bool(p.get("reviewed")) for p in state["pairs"]),
        "blocking": counts.get("blocking", 0),
        "actionable": counts.get("actionable", 0),
        "informational": counts.get("informational", 0),
        "recorded_blocking": recorded.get("blocking", 0),
        "recorded_actionable": recorded.get("actionable", 0),
        "recorded_informational": recorded.get("informational", 0),
        "system_reviewed_segments": len(unreviewed_before),
    })
    state["has_blocking"] = counts.get("blocking", 0) > 0
    state["delivery_status"] = delivery.compute_delivery_status(state)
    state["stage"] = state_migration.derive_stage(state)
    state["closeout_translation_review"] = {
        "run_id": RUN_ID,
        "status": "complete",
        "reviewed_at": timestamp,
        "actor": ACTOR,
        "pre_review_state_sha256": before_hash,
        "original_actionable_findings_resolved": len(original_actionables),
        "unreviewed_segments_closed": unreviewed_before,
        "translation_targets_changed": changed,
        "system_repair_segments": sorted(SYSTEM_FLAGS),
        "historical_initial_targets_modified": False,
    }
    core.save_job_state(args.job_id, state)
    after_hash = _sha256(state_path)
    shutil.copyfile(state_path, reviewed_state_path)

    # Deterministic checks are diagnostics, not automatically accepted findings.
    check_indexes = sorted(set(changed) | set(unreviewed_before))
    check_findings = []
    for index in check_indexes:
        pair = state["pairs"][index]
        section = core._batch_section_profile(state.get("document_profile"), index, 1)
        for finding in core.check_translation_batch(
                [pair["source"]], [pair["target"]], state.get("glossary") or [],
                "Chinese", section_profile=section):
            check_findings.append({**finding, "segment_index": index})

    evidence = academic_evidence.build_academic_evidence(
        state, args.job_id, max_candidates=len(state["pairs"]))
    selected = academic_writer.select_academic_cases(
        {}, {"claims": []}, evidence, policy="authentic_only")
    eligible = [
        item["case_id"] for item in evidence.get("candidate_cases") or []
        if item.get("academic_candidate_status") == "eligible"
    ]
    audit = {
        "schema_version": "translation-review-audit-v1",
        "job_id": args.job_id,
        "generated_at": timestamp,
        "pre_review_state_sha256": before_hash,
        "post_review_state_sha256": after_hash,
        "historical_initial_targets_modified": False,
        "original_actionable_findings": len(original_actionables),
        "original_actionable_findings_resolved": len(dispositions),
        "disposition_distribution": dict(sorted(Counter(
            item["disposition"] for item in dispositions).items())),
        "dispositions": dispositions,
        "unreviewed_before": unreviewed_before,
        "unreviewed_after": [
            i for i, pair in enumerate(state["pairs"]) if not pair.get("reviewed")],
        "changed_segment_indexes": changed,
        "system_repair_segments": sorted(SYSTEM_FLAGS),
        "system_repair_eligibility": "permanently_excluded_by_persisted_integrity_flags",
        "focused_deterministic_findings": check_findings,
        "open_findings_after": dict(sorted(counts.items())),
        "recorded_findings_after": dict(sorted(recorded.items())),
        "academically_eligible_revision_case_ids": eligible,
        "generic_authentic_selection": selected,
    }
    audit["content_hash"] = academic_evidence.stable_hash(
        {k: v for k, v in audit.items() if k != "content_hash"})
    _write(audit_path, audit)

    report = f"""# 翻译审校收口报告

- 原有 actionable finding：{len(original_actionables)} 条，已逐条裁决 {len(dispositions)} 条
- 裁决分布：{json.dumps(audit['disposition_distribution'], ensure_ascii=False)}
- 原未审校段：{len(unreviewed_before)} 段；当前未审校段：{len(audit['unreviewed_after'])} 段
- 实际更新终译：{len(changed)} 段
- 当前 blocking/actionable：{counts.get('blocking', 0)}/{counts.get('actionable', 0)}
- 历史初译是否修改：否

## 系统故障与论文案例边界

- 0001、0093、0101、0201：全量对齐补遗发现作者名误译和相邻段复制；已恢复对应译文，永久排除。
- 0014：章节标题与正文同名影片的已核验译名不一致；已统一为《牢狱大暴动》，永久排除。
- 0142：历史终译吞入0143内容；已按PDF跨页断句修复，永久排除出真实修订案例。
- 0144/0145：源句跨段且0144带模型JSON外壳；已清理并重切分，永久排除。
- 0209：`RIOT IN CELL BLOCK 11`是源文真实标题；历史初译来自0208、历史终译未翻译。现译为《牢狱大暴动》，仍永久排除。
- 0236、0239：历史译文分别复制相邻段内容；已恢复对应译文，永久排除。

## Finding裁决原则

- 接受并修复：29条；只修改可由源文和上下文直接验证的语言问题。
- 驳回误报：2条；不机械回填英文专名，也不把源文已有关系误判为译文增译。
- 纠正错挂：1条；保留0152历史finding不动，另在0151建立真实问题记录并修复。

## 后续门禁

本轮产生的真实语言修订可按共享资格规则重新审计。带持久完整性标记的系统修复无论文字是否已正确，都不得进入核心案例。作者问题保持撤回，不生成或模拟任何作者意图。
"""
    report_path.write_text(report, encoding="utf-8")
    manifest = {
        "schema_version": "translation-review-run-v1",
        "run_id": RUN_ID,
        "job_id": args.job_id,
        "state_path": str(state_path),
        "backup_path": str(backup_path),
        "reviewed_state_path": str(reviewed_state_path),
        "state_sha256_before": before_hash,
        "state_sha256_after": after_hash,
        "status": "complete" if not audit["unreviewed_after"]
        and counts.get("blocking", 0) == 0 and counts.get("actionable", 0) == 0
        and not check_findings else "review_required",
        "artifact_files": [
            backup_path.name, reviewed_state_path.name, audit_path.name,
            report_path.name, manifest_path.name],
    }
    _write(manifest_path, manifest)
    print(out_dir)
    return 0 if manifest["status"] == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
