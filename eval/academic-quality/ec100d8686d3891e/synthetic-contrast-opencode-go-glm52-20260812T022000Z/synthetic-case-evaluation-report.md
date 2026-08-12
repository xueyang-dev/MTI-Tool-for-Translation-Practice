# Synthetic Contrast Case Evaluation

- job: `ec100d8686d3891e`
- authentic cases retained: 0209, 0272
- synthetic cases selected: 1
- synthetic pipeline status: `complete`
- historical state modified: no

## Run metrics

- total_source_segments_scanned: 273
- screened_for_difficulty: 16
- difficulty_opportunities_found: 3
- synthetic_baselines_generated: 3
- baselines_rejected_as_implausible: 1
- errors_rejected_as_non_material: 1
- repairs_rejected: 0
- academically_eligible_synthetic_cases: 1

## Selected synthetic cases

### SC-0141

- Source: After Israel’s tenth anniversary celebrations, in the spring of 1958, he told me how he once said to Berl Katznelson, a founder of Labor Zionism: “What do you need that Ben-Gurion for?”
- Difficulty: This rhetorical question conveys dismissiveness toward Ben-Gurion, implying he is unnecessary or problematic. The pragmatics are confrontational and colloquial. A translator may render it as a genuine information-seeking question or soften the dismissive edge, losing the political tension.
- Synthetic Initial Translation: 在1958年春天以色列建国十周年庆典之后，他告诉我有一次他对劳工锡安主义的创始人贝尔·卡茨内尔森说：“你为什么需要那个本-古里安？”
- Why It Is Plausible: The translation '你为什么需要那个本-古里安？' is grammatically correct and faithful to the literal meaning. The use of '那个' (that) even carries a faintly dismissive tone. A competent translator could plausibly produce this neutral-sounding rendering without fully capturing the rhetorical force of the original.
- Error Diagnosis: The baseline renders 'What do you need that Ben-Gurion for?' as '你为什么需要那个本-古里安？', which is grammatically correct but pragmatically flattened. The original is a colloquial, dismissive rhetorical question—roughly 'What's the point of that Ben-Gurion?'—implying Ben-Gurion is superfluous or meddlesome. The Chinese '你为什么需要…' reads as a neutral, information-seeking inquiry ('Why do you need…?'), draining the contemptuous, confrontational force. The demonstrative '那个' (that) does carry a faint dismissive coloring, but the formal, written register of '你为什么需要' overwhelms it. A more faithful rendering would use colloquial phrasing such as '你要那个本-古里安干什么？' or '那个本-古里安有什么用？', which preserves the rhetoric
- Optimized Translation: 在1958年春天以色列建国十周年庆典之后，他告诉我有一次他对劳工锡安主义的创始人贝尔·卡茨内尔森说：“你要那个本-古里安干什么？”
- Actual Delta: {"changed": true, "changes": [{"operation": "delete", "baseline": "为什么需", "optimized": ""}, {"operation": "insert", "baseline": "", "optimized": "干什么"}]}
- Repair Validation: The source 'What do you need that Ben-Gurion for?' is a colloquial, dismissive rhetorical question. The baseline '你为什么需要那个本-古里安？' is syntactically faithful but reads as a neutral information-seeking inquiry, flattening the contemptuous pragmatic force. The optimized '你要那个本-古里安干什么？' uses the colloquial '要……干什么' rhetorical structure, restoring the dismissive, confrontational register without altering the propositional content. The repair is well-grounded and adds meaningful pragmatic value.
- Academic Value: medium
- Theory Potential: 可用于解释该错误机制与修复关系；连接具体理论前仍需 Literature Evidence。
- Limitations: 模拟初译不代表作者的历史译文。; 该案例只展示一种合理的失败模式，不证明其在人类译者中的发生频率。

## Rejected synthetic cases

- SC-0133: baseline_already_adequate
- SC-0234: baseline_implausible

## Authentic / synthetic comparison

| Dimension | Authentic revisions 0209/0272 | Synthetic contrasts |
|---|---|---|
| Evidence provenance | Saved historical initial/final evidence | Analysis-generated baseline and AI optimization |
| Analysis strength | Direct evidence of an actual change; rationale may be missing | Clear controlled error/repair mechanism after validation |
| Historical process claims | Supported only to the extent recorded | Not supported |
| Error and repair clarity | Depends on surviving project records | Explicitly constructed and independently checked |
| Theory use | Requires grounded Literature Evidence | Also requires grounded Literature Evidence |
| Limitation | Sparse process rationale | No empirical human-error frequency inference |

The two case types are complementary. Synthetic cases broaden mechanism analysis but do not become revision history.
