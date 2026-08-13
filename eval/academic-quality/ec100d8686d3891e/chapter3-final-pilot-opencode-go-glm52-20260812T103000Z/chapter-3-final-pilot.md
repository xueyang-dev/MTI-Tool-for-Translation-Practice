# 第三章 翻译问题的层级化修订与受控对比

## 3 翻译问题的层级化修订与受控对比

# 3 翻译问题的层级化修订与受控对比

### 3.1 证据边界与分析路径

<!--rq:RQ1--> <!--rq:RQ2-->
本章以源译对应、话语指称和语用力度为递进主线，先分析两项真实修订，再以 SC-0141 作为补充性受控对比。现有项目证据仅支持 2 个通过修订资格门禁的真实修订案例；未用弱证据或无真实修订的片段补足第三个案例。<!--case-count-policy:two_case_fallback--> 为考察可能偏差，构造如下模拟初译作为补充性受控对比，合成对比案例以真实源文为基础，模拟初译与优化译文均为分析阶段生成，不代表作者的历史翻译；其合理性、错误实质性与修复有效性分别经过检查。<!--synthetic-methodology--> 合成案例只能展示合理的翻译失败模式，不能证明此类错误在人类译者中的实际发生频率。<!--synthetic-limitation-->

在分析路径上，本章严格区分历史修订事实与作者分析。对于真实修订案例，仅依据项目记录中留存的源文、历史初译与历史终译进行文本层面的差异比对，不推断未记录的译者意图或审校过程。对于合成对比案例，则明确界定其为受控生成的分析材料，旨在补充真实修订证据中缺失的语用力度维度分析。通过这种层级化的证据约束设计，本章试图在不越界的前提下，揭示翻译问题在不同维度上的表现与修复机制。

### 3.2 真实修订案例：对应关系与话语指称

### 案例 seg-ec100d8686d3891e-0209（revision_case；partial_process_evidence）

- **翻译问题**：历史初译文本与本段源文在语言和内容上都无对应关系。源文为英文题名，而初译产出了一段描述时间与季节的中文陈述，两者在信息结构上完全断裂。
- **源文**：
> [SOURCE seg-ec100d8686d3891e-0209]: RIOT IN CELL BLOCK 11
- **历史初译**：
> [INITIAL seg-ec100d8686d3891e-0209]: 那是夏天，或是夏末。那是午后。
- **finding/文本差异**：无
- **实际修订**：将无对应关系的中文片段整体替换为源文题名
- **历史终译**：
> [TARGET seg-ec100d8686d3891e-0209]: RIOT IN CELL BLOCK 11
- **备选（counterfactual_rendering）**：若保留初译“那是夏天，或是夏末。那是午后。”，则该段与源文题名“RIOT IN CELL BLOCK 11”仍无对应关系，信息结构错配将持续存在。
- **备选（analytical_comparison）**：终译直接保留英文题名“RIOT IN CELL BLOCK 11”未作中文翻译，但现有记录不能证明保留英文是有意的最终翻译策略，也可能仅是临时占位。
- **决策理由**：可观察到的修订是将无对应关系的中文片段整体替换为源文题名，客观上恢复了当前段的源译对应；但保留英文题名的原因未记录。
- **翻译效果**：information_structure（依据：“那是夏天，或是夏末。那是午后。”与题名源文无对应，终译“RIOT IN CELL BLOCK 11”与本段源文一致。）
- **理论连接**：not_applicable
- **证据边界与有界结论**：该修订恢复了本段的源译对应，但现有证据既不说明初译错配的生成机制，也不证明保留英文题名是有意翻译策略。
- **需要人工证据**：保留英文题名而不译出的原因。初译为何出现与本段无对应关系文本的工作流记录。
<!--claim:C1-->

### 案例 seg-ec100d8686d3891e-0272（revision_case；partial_process_evidence）

- **翻译问题**：源文显式使用 “Those five words” 回指前文引语，但不得据此声称可见英文引语恰好五词；在汉译中，“你不会经历战争”为七个汉字，初译“这五个字”因此在目标语表层产生可直接核对的不一致。
- **源文**：
> [SOURCE seg-ec100d8686d3891e-0272]: “You will not have a war,” Matti suddenly said. Those five words have echoed within me for fifty years.
- **历史初译**：
> [INITIAL seg-ec100d8686d3891e-0272]: “你不会经历战争，”马蒂突然说道。这五个字在我心中回响了五十年。
- **finding/文本差异**：无
- **实际修订**：“五个字”至“这句话”替换
- **历史终译**：
> [TARGET seg-ec100d8686d3891e-0272]: “你不会经历战争，”马蒂突然说道。这句话在我心中回响了五十年。
- **备选（counterfactual_rendering）**：若保留初译“这五个字”，则该数字指称与七字中文引语在目标语表层仍存在可直接核对的不一致。
- **备选（analytical_comparison）**：终译“这句话”以整句指称替代数字指称，避免了“五个字”与七字引语的表层矛盾，但同时也丢失了源文以精确数字回指所带来的修辞效果。
- **决策理由**：可观察到的“五个字”至“这句话”替换，客观上消除了“五个字”与七字中文引语的表层不一致，使回指对象变为整句言语；历史动机未记录。
- **翻译效果**：reference_clarity（依据：将“五个字”替换为“句话”，使回指不再依赖与七字中文引语不符的目标语计数，而改为指向整句言语。）
- **理论连接**：not_applicable
- **证据边界与有界结论**：本案例只证明“五个字”至“这句话”的实际替换及其消除目标语表层计数不一致的效果；不解释源文为何使用 five，也不推断修订者动机。
- **需要人工证据**：译者关于“五个字”改为“这句话”的修订动因说明，译者是否意识到英文词数与中文字数差异的说明，编辑审校记录中关于该处修改的批注。
<!--claim:C2-->

### 3.3 合成对比案例：语用力度的补充性受控检验

### 案例 SC-0141（synthetic_contrast；非历史证据）

- **翻译难点**：源文“What do you need that Ben-Gurion for?”是口语化、带有轻蔑色彩的反问句，暗示本-古里安多余或碍事；模拟初译“你为什么需要那个本-古里安？”将其译为中性信息寻求疑问句，丢失了原文的对抗性语用力度。
- **真实源文**：
> [SYNTHETIC_SOURCE SC-0141]: After Israel’s tenth anniversary celebrations, in the spring of 1958, he told me how he once said to Berl Katznelson, a founder of Labor Zionism: “What do you need that Ben-Gurion for?”
- **合理模拟错误**：模拟初译“你为什么需要那个本-古里安？”在语法上忠实于源文句法结构“What do you need X for?”，但将口语化反问句译为正式中性疑问句，“你为什么需要”读作真诚的信息寻求，削弱了原文轻蔑、质问的语用力度。指示词“那个”虽带有轻微贬义色彩，但“你为什么需要”的正式书面语体压过了它。
- **模拟初译**：
> [SIMULATED SC-0141]: 在1958年春天以色列建国十周年庆典之后，他告诉我有一次他对劳工锡安主义的创始人贝尔·卡茨内尔森说：“你为什么需要那个本-古里安？”
- **错误诱因与诊断**：The baseline renders 'What do you need that Ben-Gurion for?' as '你为什么需要那个本-古里安？', which is grammatically correct but pragmatically flattened. The original is a colloquial, dismissive rhetorical question—roughly 'What's the point of that Ben-Gurion?'—implying Ben-Gurion is superfluous or meddlesome. The Chinese '你为什么需要…' reads as a neutral, information-seeking inquiry ('Why do you need…?'), draining the contemptuous, confrontational force. The demonstrative '那个' (that) does carry a faint dismissive coloring, but the formal, written register of '你为什么需要' overwhelms it. A more faithful rendering would use colloquial phrasing such as '你要那个本-古里安干什么？' or '那个本-古里安有什么用？', which preserves the rhetoric
- **意义/功能失真**：The original line functions as a politically charged, dismissive quip that conveys the speaker's low opinion of Ben-Gurion. By rendering it as a neutral question, the baseline softens the interpersonal and political tension, making the speaker sound genuinely curious rather than contemptuous. This shifts the characterization of the speaker and the emotional texture of the anecdote.
- **AI 优化**：将中性疑问句“你为什么需要那个本-古里安？”改为口语化反问句“你要那个本-古里安干什么？”，以还原原文轻蔑、质问的语用力度，体现说话者对本-古里安存在必要性的不屑。
- **优化译文**：
> [OPTIMIZED SC-0141]: 在1958年春天以色列建国十周年庆典之后，他告诉我有一次他对劳工锡安主义的创始人贝尔·卡茨内尔森说：“你要那个本-古里安干什么？”
- **修复机制与有效性**：The source 'What do you need that Ben-Gurion for?' is a colloquial, dismissive rhetorical question. The baseline '你为什么需要那个本-古里安？' is syntactically faithful but reads as a neutral information-seeking inquiry, flattening the contemptuous pragmatic force. The optimized '你要那个本-古里安干什么？' uses the colloquial '要……干什么' rhetorical structure, restoring the dismissive, confrontational register without altering the propositional content. The repair is well-grounded and adds meaningful pragmatic value.
- **备选（analytical_comparison）**：优化译文“你要那个本-古里安干什么？”使用口语反问结构“要……干什么”，在命题内容不变的前提下恢复了原文轻蔑、质问的语用力度，体现了说话者对本-古里安存在必要性的不屑。
- **备选（counterfactual_rendering）**：另一可能译法“那个本-古里安有什么用？”同样以反问结构传达轻蔑语气，但语体略偏评价而非直接质问。
- **决策理由**：该受控对比已通过验证：源文“What do you need that Ben-Gurion for?”在英语中为口语化、轻蔑的反问句，暗示本-古里安多余或碍事。模拟初译“你为什么需要那个本-古里安？”语法正确但语用力度被削弱，读作中性信息寻求。优化译文“你要那个本-古里安干什么？”以口语反问结构“要……干什么”恢复轻蔑、对抗性语调，且未改变命题内容。该对比为分析目的生成，不代表作者历史初译。
- **翻译效果**：pragmatic_force（依据：模拟初译“你为什么需要那个本-古里安？”使用正式书面疑问结构“你为什么需要”，读作中性信息寻求；优化译文“你要那个本-古里安干什么？”使用口语反问结构“要……干什么”，恢复了原文轻蔑、质问的对抗性语用力度，命题内容近似不变。）
- **理论连接**：not_applicable
- **证据边界与有界结论**：本案例作为合成对比，展示了中性疑问结构与口语反问结构在命题内容近似不变时改变语用力度的合理失败模式：模拟初译将轻蔑反问句译为中性疑问句，削弱了原文的政治张力与人际对抗语气。该对比不代表作者历史初译，也不证明此类错误在实际翻译中的发生频率。
<!--claim:C3-->

### 3.4 跨案例综合与局限

三项材料形成从段落对应、话语指称到语用力度的递进，但历史证据与合成证据支持的结论强度必须分开。<!--claim:C4--> 真实案例支持实际修订事实，合成案例只支持一种经验证的可能失败机制。若两类证据并列为同等案例，章节会产生方法突变感。因此，本章在综合时严格遵循证据层级：案例 seg-ec100d8686d3891e-0209 仅证明源译对应关系的客观修复，不涉及翻译策略的定性；案例 seg-ec100d8686d3891e-0272 仅证明指称替换在目标语表层消除计数不一致的可观察效果，不推断译者动机；SC-0141 则在明确非历史的边界内，提供了一种语用力度失真与修复的机制分析。这种区分确保了结论的克制与可验证性。
