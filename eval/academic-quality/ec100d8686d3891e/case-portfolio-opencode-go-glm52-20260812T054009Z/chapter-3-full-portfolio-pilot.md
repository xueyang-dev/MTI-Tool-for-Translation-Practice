# 第三章 多层级翻译问题的案例组合分析

## 3.1 案例组合方法与证据边界

本章对完整项目的 273<!--stat:segments_scanned--> 个段落进行全量扫描，从 31<!--stat:candidate_count--> 个候选中选择 26<!--stat:selected_case_count--> 个案例。案例数量并非目标本身；筛选优先考虑问题覆盖、机制差异、证据质量与章节递进。

本章把证据类型与分析篇幅分开。Authentic Revision Case 只指保存了真实初译至终译变化的段落；Supporting Example 只说明当前译文与已记录审校发现；Boundary Case 用于说明证据失配或污染；Synthetic Contrast Case 则是从真实源段构造、并经过独立资格检查的分析性对比。Supporting Example 不得写成历史修订，合成案例也不得写成作者初译。

现有 Human Evidence 仍为 awaiting_author_input，且本轮没有可用 Literature Evidence。因此，本章只讨论可观察文本关系，不还原译者心理意图，也不使用未经文献落地的理论名称。

## 3.2 源译对应与信息完整性

长篇翻译首先要求段落对应、信息完整和语义角色不被破坏。

### 3.2.1 段落错配、漏译与截断

<!--portfolio-case:seg-ec100d8686d3891e-0209-->

**段落错配、漏译与截断（seg-ec100d8686d3891e-0209，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0209]: RIOT IN CELL BLOCK 11

> [TARGET_EXCERPT seg-ec100d8686d3891e-0209]: RIOT IN CELL BLOCK 11

> [INITIAL_EXCERPT seg-ec100d8686d3891e-0209]: 那是夏天，或是夏末。那是午后。

**问题与证据**：保存记录证明这里存在真实初译至终译变化，实际差异为“那是夏天，或是夏末。那是午后。”→“RIOT IN CELL BLOCK 11”。保存的初译与终译存在可核对的文本变化。

**调整机制与效果**：核对当前源段与目标段的语义覆盖，区分完整对应、跨段串入和整段漏译。该变化的可观察效果仅限当前文本关系；现有记录不支持对修订动机、选择过程或读者反应作历史断言。

**证据边界**：本例只支持保存的实际文本差异，不支持未记录的修订理由。

<!--portfolio-case:seg-ec100d8686d3891e-0239-->

**段落错配、漏译与截断（seg-ec100d8686d3891e-0239，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0239]: As Dalia walked out of Domino, a page slipped from the book she had been holding the whole time, and he picked it up. It wasn’t a page from the book; it was handwritten:

> [TARGET_EXCERPT seg-ec100d8686d3891e-0239]: 他看到苏格（Sugar）啃着鸡腿，在百万富翁游艇的床上亲吻托尼·柯蒂斯。

> [REVIEW_FINDING seg-ec100d8686d3891e-0239]: 译文将原文第二段内容错误地合并到第一段末尾，且重复了第一段中已有的句子“他看到苏格啃着鸡腿……”，导致第二段原文“As Dalia walked out of Domino, a page slipped from the book she had been holding the whole time, and he picked it up. It wasn’t a page from the book; it was handwritten:”完全漏译。

该例作为 Supporting Example，补充说明同一机制：核对当前源段与目标段的语义覆盖，区分完整对应、跨段串入和整段漏译。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

<!--portfolio-case:seg-ec100d8686d3891e-0142-->

**段落错配、漏译与截断（seg-ec100d8686d3891e-0142，tier_3_contrast_boundary）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0142]: Before Dad started the jeep, Mom said to him, “Now you’ll appreciate my coffee.” Dad laughed and replied, “That was chicory.” “What’s chicory?” I asked. Mom explained about the austerity period and Dov Yosef, who was the Minister of Rationing. On the short drive back westward, I saw Mom place her left hand on the

> [TARGET_EXCERPT seg-ec100d8686d3891e-0142]: 在爸爸发动吉普车之前，妈妈对他说：“现在你会欣赏我的咖啡了。”爸爸笑着回答：“那是菊苣。”我问：“什么是菊苣？”妈妈解释了配给时期和时任配给部长的多夫·约瑟夫。在向西返回的短途车程中，我看到妈妈把左手放在爸爸的右手背上——那只换挡的手。吉普车有三个前进挡和一个倒挡。他立刻甩开她的手，看向左边。妈妈把目光转向右边。我无法忘记这一幕。爸爸去世后，我问妈妈那次去菊苣地的旅行。“你在说什么？”她说，“我们和露丝、阿扎里亚连朋友都不是。而且贝特哈希塔属于基布兹联合派系，谁会跟他们说话？”她说完就转过身去，背对着我这个三岁半的孩子。我想，你不该和菊苣争论，但没说出口。

该例仅用于说明证据边界：probable_adjacent_target_overlap; probable_source_truncation。由于 finding、段落边界或目标文本存在来源一致性问题，本例不支持翻译策略、修订效果或译者意图结论。

<!--portfolio-case:seg-ec100d8686d3891e-0144-->

**段落错配、漏译与截断（seg-ec100d8686d3891e-0144，tier_3_contrast_boundary）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0144]: We were nine years old. It was spring. The poppies were in bloom, and so were the chrysanthemums. Back then, we didn’t know it happened six months before Operation Kadesh, which was in 1956. Dad drove from the valley to the Negev, near Gaza, to harvest hay in the fields of Nahal Oz. This time, he took me with him. He asked for and received permission from my…

> [TARGET_EXCERPT seg-ec100d8686d3891e-0144]: ```json [   "我们九岁。那是春天。罂粟花开了，菊花也开了。那时，我们并不知道这发生在卡迭石行动（1956年）前六个月。爸爸从山谷开车到内盖夫，靠近加沙，去纳哈尔奥兹的田里收割干草。这一次，他带上了我。他向我的老师拉结请求并获得了许可，她把手放在我的头上，看着我的眼睛，听了听我的呼吸。“没有哮喘。而且也是篝火节。没问题。”天还黑着，我们都还在睡梦中，爸爸叫醒了我。“刷牙，泽维克。”“其他人呢？”我问。“只有你一个去。”爸爸回答。他三十五岁，三十五岁。我三十五岁时在哪里？第一次黎巴嫩战争。五次战争之后。我坐在吉普车的右边。我记得烧汽油的味道，以及日出前的那一刻，爸爸关掉了车灯。罂粟的红和菊花的黄让位给了亚麻的粉和矢车菊的蓝。爸爸唱着参孙的狐狸在夜里带着火把的故事，还说吉普车里最重要的是速度、离合器和倒挡…

该例仅用于说明证据边界：probable_source_truncation; serialized_model_output_in_target。由于 finding、段落边界或目标文本存在来源一致性问题，本例不支持翻译策略、修订效果或译者意图结论。

**跨案例发现**：核对当前源段与目标段的语义覆盖，区分完整对应、跨段串入和整段漏译。

### 3.2.2 审校证据与段落边界

<!--portfolio-case:seg-ec100d8686d3891e-0152-->

**审校证据与段落边界（seg-ec100d8686d3891e-0152，tier_3_contrast_boundary）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0152]: After dinner, I crossed Wadi Seder westward again to meet Irit. I had been in love with her since we studied together at the end of elementary school.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0152]: 晚饭后，我再次向西穿过Wadi Seder去与Irit见面。自从小学快毕业时我们一同学习起，我就一直爱着她。

该例仅用于说明证据边界：finding_segment_mismatch。由于 finding、段落边界或目标文本存在来源一致性问题，本例不支持翻译策略、修订效果或译者意图结论。

**跨案例发现**：先确认 finding、源段和目标段属于同一证据单元，再决定能否进入分析。

## 3.3 词汇语义与形象表达

词义选择、搭配和比喻处理共同决定叙事细节是否准确。

### 3.3.1 语境化词义与搭配

<!--portfolio-case:seg-ec100d8686d3891e-0057-->

**语境化词义与搭配（seg-ec100d8686d3891e-0057，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0057]: The red light at the tip of his left wing slowly drifts away from me, just as it should. What a pilot. Brilliant.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0057]: 他左翼尖端的红灯缓缓离我而去，正如预期那般。多么出色的飞行员。才华横溢。

> [REVIEW_FINDING seg-ec100d8686d3891e-0057]: 原文“The red light at the tip of his left wing slowly drifts away from me”中“drifts away”强调缓慢飘离的动态感，译文“缓缓离我而去”虽准确但“离我而去”略带拟人化，与后文“正如预期那般”的客观描述稍显不协调，建议改为“缓缓飘离我而去”以更贴合原文的物理动态。

**问题界定**：当前译文呈现了已被审校记录指出的问题。原文“The red light at the tip of his left wing slowly drifts away from me”中“drifts away”强调缓慢飘离的动态感，译文“缓缓离我而去”虽准确但“离我而去”略带拟人化，与后文“正如预期那般”的客观描述稍显不协调，建议改为“缓缓飘离我而去”以更贴合原文的物理动态。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：依据领域语境和搭配限制选择目标语表达，而不是沿用表面词义。

**分析性方案与预期效果**：审校记录已指出可调整的表达方向，但未保存实际采用的新译文。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

<!--portfolio-case:seg-ec100d8686d3891e-0056-->

**语境化词义与搭配（seg-ec100d8686d3891e-0056，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0056]: “You are on your own,” I inform him over a frequency that only he and I can hear now.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0056]: “你现在独自飞行了，”我在只有我们两人能听到的无线电频率上告诉他。

> [REVIEW_FINDING seg-ec100d8686d3891e-0056]: 原文“You are on your own”在飞行语境中意为“你只能靠自己了/你独自应对”，译文“你现在独自飞行了”略显生硬，且“飞行”一词可能被误解为字面动作，建议调整为更自然的表达。

该例作为 Supporting Example，补充说明同一机制：依据领域语境和搭配限制选择目标语表达，而不是沿用表面词义。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

<!--portfolio-case:seg-ec100d8686d3891e-0080-->

**语境化词义与搭配（seg-ec100d8686d3891e-0080，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0080]: But the magnificent, spherical artificial horizon of the Kurnass tells a completely different story.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0080]: 但是，Kurnass 那宏伟的球形人工地平仪却讲述了一个完全不同的故事。

> [REVIEW_FINDING seg-ec100d8686d3891e-0080]: “宏伟的”修饰人工地平仪不够贴切，原文 magnificent 在此语境下更强调其醒目、壮观，建议改为“壮观的”或“醒目的”。

该例作为 Supporting Example，补充说明同一机制：依据领域语境和搭配限制选择目标语表达，而不是沿用表面词义。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

<!--portfolio-case:seg-ec100d8686d3891e-0081-->

**语境化词义与搭配（seg-ec100d8686d3891e-0081，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0081]: The plane is in a gentle left turn, the nose right on the horizon.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0081]: 飞机正在温和地左转，机头正好对准地平线。

> [REVIEW_FINDING seg-ec100d8686d3891e-0081]: “温和地左转”中“温和”用于描述飞机转弯不够自然，建议改为“平缓地左转”或“轻微左转”。

该例作为 Supporting Example，补充说明同一机制：依据领域语境和搭配限制选择目标语表达，而不是沿用表面词义。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

**跨案例发现**：依据领域语境和搭配限制选择目标语表达，而不是沿用表面词义。

### 3.3.2 比喻与形象表达

<!--portfolio-case:seg-ec100d8686d3891e-0139-->

**比喻与形象表达（seg-ec100d8686d3891e-0139，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0139]: Back then, Dad wasn’t building houses yet; he was repairing machines. Even then, I think I already sensed that he did things I would never be able to do. Many years later, I asked him to teach me how to weld. “What do you need that for?” he replied, as was his way, once again evading the outstretched hand.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0139]: 那时，父亲还未开始建造房屋，他还在修理机器。即便在那时，我想我已隐约感觉到，他所做的事情是我永远无法企及的。多年以后，我请他教我焊接技术，他却以他一贯的方式回答：“你需要那个做什么？”再次避开了我伸出的手。

> [REVIEW_FINDING seg-ec100d8686d3891e-0139]: 译文将“as was his way, once again evading the outstretched hand”译为“他却以他一贯的方式回答……再次避开了我伸出的手”，将“evading the outstretched hand”直译，但原文中“outstretched hand”是比喻（指请求），译文“伸出的手”略显生硬，建议调整为更自然的表达。

> [REVIEW_SUGGESTION seg-ec100d8686d3891e-0139]: 他却以他一贯的方式回答：“你需要那个做什么？”再次回避了我的请求。

**问题界定**：当前译文呈现了已被审校记录指出的问题。译文将“as was his way, once again evading the outstretched hand”译为“他却以他一贯的方式回答……再次避开了我伸出的手”，将“evading the outstretched hand”直译，但原文中“outstretched hand”是比喻（指请求），译文“伸出的手”略显生硬，建议调整为更自然的表达。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：识别字面动作背后的隐喻功能，并在目标语中保留其叙事作用。

**分析性方案与预期效果**：审校记录给出的分析性备选是“他却以他一贯的方式回答：“你需要那个做什么？”再次回避了我的请求。”。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

**跨案例发现**：识别字面动作背后的隐喻功能，并在目标语中保留其叙事作用。

### 3.3.3 标题语义与形式

<!--portfolio-case:seg-ec100d8686d3891e-0119-->

**标题语义与形式（seg-ec100d8686d3891e-0119，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0119]: In Praise of Perplexion and the Condemnation of Certainty

> [TARGET_EXCERPT seg-ec100d8686d3891e-0119]: 颂扬困惑，谴责确定性

> [REVIEW_FINDING seg-ec100d8686d3891e-0119]: 原文标题为并列结构，译文用逗号分隔略显松散，且“确定性”一词在哲学语境下可更精确。建议保持原文的对称结构，并考虑“确定性”译为“笃定”更贴合语境。

**问题界定**：当前译文呈现了已被审校记录指出的问题。原文标题为并列结构，译文用逗号分隔略显松散，且“确定性”一词在哲学语境下可更精确。建议保持原文的对称结构，并考虑“确定性”译为“笃定”更贴合语境。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：同时处理标题的语义核心、并列结构与文体凝练度。

**分析性方案与预期效果**：审校记录已指出可调整的表达方向，但未保存实际采用的新译文。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

**跨案例发现**：同时处理标题的语义核心、并列结构与文体凝练度。

## 3.4 句法组织与逻辑关系

修饰范围、论元关系和显隐逻辑需要按目标语重新组织。

### 3.4.1 修饰范围

<!--portfolio-case:seg-ec100d8686d3891e-0170-->

**修饰范围（seg-ec100d8686d3891e-0170，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0170]: We were nineteen. It was summer, or the end of it. The snapdragon and fennel were blooming, white and yellow. Someone from the team, wearing a knitted kippah on his head, showed us that you could eat fennel leaves, and they really were tasty – anise.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0170]: 我们当时十九岁。正值夏天，或是夏末时节。金鱼草和茴香花盛开，白色与黄色交织。队伍中一位头戴针织圆顶小帽的同伴告诉我们，茴香的叶子可以食用，尝起来确实美味——带着茴芹的香气。

> [REVIEW_FINDING seg-ec100d8686d3891e-0170]: 原文“The snapdragon and fennel were blooming, white and yellow”中“white and yellow”修饰的是两种花（金鱼草和茴香）的颜色，译文“白色与黄色交织”暗示颜色混合交织，与原文并列描述不符，建议改为“白色和黄色”。

**问题界定**：当前译文呈现了已被审校记录指出的问题。原文“The snapdragon and fennel were blooming, white and yellow”中“white and yellow”修饰的是两种花（金鱼草和茴香）的颜色，译文“白色与黄色交织”暗示颜色混合交织，与原文并列描述不符，建议改为“白色和黄色”。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：明确修饰语实际辖域，避免目标语把并列属性误写成混合关系。

**分析性方案与预期效果**：审校记录已指出可调整的表达方向，但未保存实际采用的新译文。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

**跨案例发现**：明确修饰语实际辖域，避免目标语把并列属性误写成混合关系。

### 3.4.2 逻辑关系的显化与增删

<!--portfolio-case:seg-ec100d8686d3891e-0171-->

**逻辑关系的显化与增删（seg-ec100d8686d3891e-0171，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0171]: This hike was the highlight of the preparatory phase of the flying course. We had already finished that legendary run that sent some of us to the hospital.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0171]: 这次徒步是飞行课程预备阶段中最精彩的部分。我们已经完成了那次传奇长跑，有些人因此被送进了医院。

> [REVIEW_FINDING seg-ec100d8686d3891e-0171]: 原文“that legendary run”中的“that”指代前文已提及或双方共知的事件，译文“那次传奇长跑”虽保留指代，但“传奇”一词略显口语化，学术书面语中可考虑“那次著名的长跑”，但原译尚可接受；更主要的问题是“sent some of us to the hospital”译为“有些人因此被送进了医院”，其中“因此”增加了因果关系，原文仅陈述事实，建议去掉“因此”以更贴近原文。

**问题界定**：当前译文呈现了已被审校记录指出的问题。原文“that legendary run”中的“that”指代前文已提及或双方共知的事件，译文“那次传奇长跑”虽保留指代，但“传奇”一词略显口语化，学术书面语中可考虑“那次著名的长跑”，但原译尚可接受；更主要的问题是“sent some of us to the hospital”译为“有些人因此被送进了医院”，其中“因此”增加了因果关系，原文仅陈述事实，建议去掉“因此”以更贴近原文。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：只显化源文能够支持的逻辑关系，避免无依据增加因果或评价。

**分析性方案与预期效果**：审校记录已指出可调整的表达方向，但未保存实际采用的新译文。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

**跨案例发现**：只显化源文能够支持的逻辑关系，避免无依据增加因果或评价。

### 3.4.3 论元关系与句法重组

<!--portfolio-case:seg-ec100d8686d3891e-0234-->

**论元关系与句法重组（seg-ec100d8686d3891e-0234，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0234]: Then she said, ‘Amos, give me enough for the tickets and drop us off at the Palace. What do you say? We’re not kids anymore.’ Amos looked at her and without smiling, said, ‘No way. Absolutely not. Everyone stays together.’ And Tzvika, who always played basketball with Ami and milked the goats with him, said he was changing his vote in favor of the Palace … a…

> [TARGET_EXCERPT seg-ec100d8686d3891e-0234]: 然后她说：“阿莫斯，给我们足够的票钱，送我们去皇宫影院吧。你觉得怎么样？我们不再是孩子了。”阿莫斯看着她，没有微笑，说：“不行，绝对不行。大家必须在一起。”而茨维卡，那个总是和阿米一起打篮球、和他一起挤羊奶的人，说他改变主意，支持去皇宫影院……并笑了起来。阿莫斯说，一旦投票结束，任何人都不能改变主意，否则就没完没了了。于是我们前往多米诺影院。

> [REVIEW_FINDING seg-ec100d8686d3891e-0234]: “give me enough for the tickets”译为“给我们足够的票钱”语义不完整，原文是“给我足够的钱买票”，建议调整为“给我够买票的钱”。

**问题界定**：当前译文呈现了已被审校记录指出的问题。“give me enough for the tickets”译为“给我们足够的票钱”语义不完整，原文是“给我足够的钱买票”，建议调整为“给我够买票的钱”。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：重建动词与施受事、数量或用途成分之间的关系。

**分析性方案与预期效果**：审校记录已指出可调整的表达方向，但未保存实际采用的新译文。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

**跨案例发现**：重建动词与施受事、数量或用途成分之间的关系。

## 3.5 术语、专名与文化指称

专业术语与专名处理必须同时满足领域准确性和全篇一致性。

### 3.5.1 专业术语与技术规范

<!--portfolio-case:seg-ec100d8686d3891e-0059-->

**专业术语与技术规范（seg-ec100d8686d3891e-0059，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0059]: Eight thousand feet, three hundred and twenty knots, heading 285, the horizon steady. The cursed horizon of the Mystère. Even the Magister had a better artificial horizon.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0059]: 八千英尺高度，三百二十节速度，航向285，地平线平稳。这该死的“神秘”式地平线。就连“教师”式飞机的人工地平仪都比它好。

> [REVIEW_FINDING seg-ec100d8686d3891e-0059]: 原文“heading 285”在飞行术语中通常指航向285度，译文“航向285”省略了“度”，虽可理解但不够规范，建议补充“度”以符合中文技术表达习惯。

**问题界定**：当前译文呈现了已被审校记录指出的问题。原文“heading 285”在飞行术语中通常指航向285度，译文“航向285”省略了“度”，虽可理解但不够规范，建议补充“度”以符合中文技术表达习惯。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：按领域意义和中文技术表达规范处理术语、单位与固定搭配。

**分析性方案与预期效果**：审校记录已指出可调整的表达方向，但未保存实际采用的新译文。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

<!--portfolio-case:seg-ec100d8686d3891e-0082-->

**专业术语与技术规范（seg-ec100d8686d3891e-0082，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0082]: I am in vertigo, with Shaul sitting in the rear cockpit.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0082]: 我正处于空间定向障碍中，而 Shaul 坐在后座舱里。

> [REVIEW_FINDING seg-ec100d8686d3891e-0082]: “空间定向障碍”虽为专业术语，但原文 vertigo 在飞行语境中常译为“眩晕”或“空间迷失”，且“我正处于空间定向障碍中”略显生硬，建议改为“我出现了空间定向障碍”。

该例作为 Supporting Example，补充说明同一机制：按领域意义和中文技术表达规范处理术语、单位与固定搭配。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

**跨案例发现**：按领域意义和中文技术表达规范处理术语、单位与固定搭配。

### 3.5.2 人名、地名与机构名一致性

<!--portfolio-case:seg-ec100d8686d3891e-0215-->

**人名、地名与机构名一致性（seg-ec100d8686d3891e-0215，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0215]: He tried to tan, but his skin turned red. He walked with the older kids toward Atlit and back, collected a lot of seashells, and found one that echoed the sound of the sea when he held it to his ear. He also found a rare one, a dark shell, that only he had until the end of camp. He refused to trade it, remembering what had happened on the trip to the Rabbits…

> [TARGET_EXCERPT seg-ec100d8686d3891e-0215]: 他试着晒黑，但皮肤却变红了。他和年长的孩子们一起走到阿特利特再折返，收集了许多贝壳，还找到一个贴在耳边能回响海声的。他还发现了一个稀有的深色贝壳，直到营地结束前只有他拥有。他拒绝交换，想起了去兔子藏身处和椅子山的旅行中发生的事。在那里，他找到了一盏真正古老的油灯，完好无损，但他们却换给他一个毫无价值的。油灯的故事——那是很久以前的事了。

> [REVIEW_FINDING seg-ec100d8686d3891e-0215]: 原文中“Atlit”是地名，应保留原文；另外“Rabbits Hideaway”和“Chair Hill”是专有地名，应保留原文或加注中文译名并保留原文。

> [REVIEW_SUGGESTION seg-ec100d8686d3891e-0215]: 他试着晒黑，但皮肤却变红了。他和年长的孩子们一起走到Atlit再折返，收集了许多贝壳，还找到一个贴在耳边能回响海声的。他还发现了一个稀有的深色贝壳，直到营地结束前只有他拥有。他拒绝交换，想起了去Rabbits Hideaway和Chair Hill的旅行中发生的事。在那里，他找到了一盏真正古老的油灯，完好无损，但他们却换给他一个毫无价值的。油灯的故事——那是很久以前的事了。

**问题界定**：当前译文呈现了已被审校记录指出的问题。原文中“Atlit”是地名，应保留原文；另外“Rabbits Hideaway”和“Chair Hill”是专有地名，应保留原文或加注中文译名并保留原文。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：依据全篇命名政策统一音译、原文保留和首次标注方式。

**分析性方案与预期效果**：审校记录给出的分析性备选是“他试着晒黑，但皮肤却变红了。他和年长的孩子们一起走到Atlit再折返，收集了许多贝壳，还找到一个贴在耳边能回响海声的。他还发现了一个稀有的深色贝壳，直到营地结束前只有他拥有。他拒绝交换，想起了去Rabbits Hideaway和Chair Hill的旅行中发生的事。在那里，他找到了一盏真正古老的油灯，完好无损，但他们却换给他一个毫无价值的。油灯的故事——那是很久以前的事了。”。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

<!--portfolio-case:seg-ec100d8686d3891e-0140-->

**人名、地名与机构名一致性（seg-ec100d8686d3891e-0140，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0140]: Ruth served coffee and asked me, three and a half years old, how things were in Geva. Someone walked in, patted Azariah on the shoulder, and asked, “Why did they dismantle the Palmach unit, anyway?” “Ask Ben-Gurion, or Tabenkin,” Azariah replied without a smile. For a moment, there was a sense of sorrow in that small room in Beit HaShita, which held a painti…

> [TARGET_EXCERPT seg-ec100d8686d3891e-0140]: 露丝端上咖啡，问我这个三岁半的孩子，格瓦（Geva）的情况如何。有人走进来，拍了拍阿扎里亚的肩膀，问道：“他们到底为什么解散了帕尔马赫部队？”“去问本-古里安，或者塔本金，”阿扎里亚没有笑容地回答。片刻间，贝特哈希塔那间小屋里弥漫着一股悲伤的气息，屋里挂着一幅古特曼画的几朵白色银莲花，但没有收音机或电话，而且和其他地方一样，没有理由锁门。

> [REVIEW_FINDING seg-ec100d8686d3891e-0140]: 译文“格瓦（Geva）”中括号保留原文，但按审校要求地名应保留原文，无需加注拼音或括号；且“贝特哈希塔”未保留原文，建议统一处理。另外“没有理由锁门”略显直译，可稍作润色。

该例作为 Supporting Example，补充说明同一机制：依据全篇命名政策统一音译、原文保留和首次标注方式。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

<!--portfolio-case:seg-ec100d8686d3891e-0141-->

**人名、地名与机构名一致性（seg-ec100d8686d3891e-0141，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0141]: “Who is Tabenkin?” I asked. That question was answered later that evening by Grandpa, Dad’s father. But he didn’t want to talk about Ben-Gurion. After Israel’s tenth anniversary celebrations, in the spring of 1958, he told me how he once said to Berl Katznelson, a founder of Labor Zionism: “What do you need that Ben-Gurion for?”

> [TARGET_EXCERPT seg-ec100d8686d3891e-0141]: “塔本金是谁？”我问。这个问题当晚晚些时候由祖父，也就是父亲的父亲，回答了。但他不想谈论本-古里安。在以色列建国十周年庆祝活动之后，1958年春天，他告诉我他曾对劳工犹太复国主义的创始人之一贝尔·卡茨内尔森说：“你要那个本-古里安干什么？”

> [REVIEW_FINDING seg-ec100d8686d3891e-0141]: 译文“贝尔·卡茨内尔森”中“贝尔”为音译，但原文“Berl”应保留原文，且“劳工犹太复国主义”建议保留原文“Labor Zionism”或加注，以符合术语一致性要求。

该例作为 Supporting Example，补充说明同一机制：依据全篇命名政策统一音译、原文保留和首次标注方式。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

<!--portfolio-case:seg-ec100d8686d3891e-0156-->

**人名、地名与机构名一致性（seg-ec100d8686d3891e-0156，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0156]: Anyone who grew up on one of the banks of that wadi knows the basalt rocks and the thorny jujube trees with their orange fruits.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0156]: 任何在河谷岸边长大的人，都熟悉那些玄武岩和多刺的枣树及其橙色果实。

> [REVIEW_FINDING seg-ec100d8686d3891e-0156]: 原文“on one of the banks of that wadi”中“wadi”是地理术语（干涸河谷），译文译为“河谷”虽可理解，但未保留原文术语；且“anyone who grew up”译为“任何在河谷岸边长大的人”略显生硬，建议调整为更自然的表达。

该例作为 Supporting Example，补充说明同一机制：依据全篇命名政策统一音译、原文保留和首次标注方式。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

<!--portfolio-case:seg-ec100d8686d3891e-0235-->

**人名、地名与机构名一致性（seg-ec100d8686d3891e-0235，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0235]: He liked Tzvika. Tzvika was the one who taught him that after ninety-nine comes a hundred. Tzvika never laughed at him when he struggled to breathe, and he certainly didn’t laugh when Noam carried him back to shore. Sometimes, Tzvika even played basketball with him, even though he wasn’t at his level – or Ami’s, and certainly not Uzi’s or Amnon’s.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0235]: 他喜欢Tzvika。Tzvika教会了他九十九之后是一百。当他呼吸困难时，Tzvika从未嘲笑过他，当然，当Noam把他背回岸边时，他也没有笑。有时，Tzvika甚至和他一起打篮球，尽管他的水平远不及他——或Ami，更不用说Uzi或Amnon了。

> [REVIEW_FINDING seg-ec100d8686d3891e-0235]: 人名“Tzvika”、“Noam”、“Ami”、“Uzi”、“Amnon”未按前文统一译名，前文已译为“茨维卡”、“诺姆”、“阿米”、“乌兹”、“阿姆农”，此处应保持一致。

该例作为 Supporting Example，补充说明同一机制：依据全篇命名政策统一音译、原文保留和首次标注方式。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

**跨案例发现**：依据全篇命名政策统一音译、原文保留和首次标注方式。

### 3.5.3 作品名与文化专名

<!--portfolio-case:seg-ec100d8686d3891e-0233-->

**作品名与文化专名（seg-ec100d8686d3891e-0233，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0233]: On the way, Amos said there were two movies in Haifa that we could see – Some Like It Hot, playing at the Palace Cinema, and Riot in Cell Block 11, showing at the Domino Cinema. The girls wanted to go to the Palace, and we wanted to go to Domino. They took a vote, and it ended in a tie – eleven girls and eleven boys. He whispered quietly, ‘Palace, Palace.’ A…

> [TARGET_EXCERPT seg-ec100d8686d3891e-0233]: 路上，阿莫斯说海法有两部电影可选——《热情如火》在皇宫影院上映，《监狱摇滚》在多米诺影院放映。女孩们想去皇宫，我们想去多米诺。他们投票表决，结果平局——十一个女孩对十一个男孩。有人轻声嘀咕：“皇宫，皇宫。”阿莫斯说平局由他定夺，我们去多米诺。有人说：“玛丽莲·梦露。”阿莫斯回应：“要是碧姬·芭铎……”诺姆插嘴：“或者罗妮·霍夫纳。”但他坐在卡车第二排靠边位置，她没听见。

> [REVIEW_FINDING seg-ec100d8686d3891e-0233]: 专有名词“Riot in Cell Block 11”的译名“监狱摇滚”不准确，该片标准译名为“监狱暴动”或“第十一牢房的暴动”；且“皇宫影院”和“多米诺影院”作为影院名，建议保留原文或加注，但此处可接受。

**问题界定**：当前译文呈现了已被审校记录指出的问题。专有名词“Riot in Cell Block 11”的译名“监狱摇滚”不准确，该片标准译名为“监狱暴动”或“第十一牢房的暴动”；且“皇宫影院”和“多米诺影院”作为影院名，建议保留原文或加注，但此处可接受。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：先确认作品或文化专名身份，再决定采用通行译名、原名或双重标注。

**分析性方案与预期效果**：审校记录已指出可调整的表达方向，但未保存实际采用的新译文。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

<!--portfolio-case:seg-ec100d8686d3891e-0216-->

**作品名与文化专名（seg-ec100d8686d3891e-0216，tier_2_supporting）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0216]: On the way back, Amos sang A State, A State for My Wandering Nation, In the Galilee at Tel Hai, and I Never Have Anything to Wear on Friday Night. The girls sang along with him, and some of the boys did too.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0216]: 归途中，阿莫斯唱起了《立国，为漂泊民族立国》《加利利在特尔海》《周五晚上我总没衣服穿》。

> [REVIEW_FINDING seg-ec100d8686d3891e-0216]: 歌曲名称《A State, A State for My Wandering Nation》《In the Galilee at Tel Hai》《I Never Have Anything to Wear on Friday Night》应保留原文，不应翻译。

该例作为 Supporting Example，补充说明同一机制：先确认作品或文化专名身份，再决定采用通行译名、原名或双重标注。它记录的是审校问题，而不是已经发生的修订；审校建议只能作为分析性备选。

**跨案例发现**：先确认作品或文化专名身份，再决定采用通行译名、原名或双重标注。

## 3.6 指称衔接、叙事声音与语用力度

篇章回指、人物声音和言语行为需要超越逐词对应进行判断。

### 3.6.1 回指与主语追踪

<!--portfolio-case:seg-ec100d8686d3891e-0272-->

**回指与主语追踪（seg-ec100d8686d3891e-0272，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0272]: “You will not have a war,” Matti suddenly said. Those five words have echoed within me for fifty years.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0272]: “你不会经历战争，”马蒂突然说道。这句话在我心中回响了五十年。

> [INITIAL_EXCERPT seg-ec100d8686d3891e-0272]: “你不会经历战争，”马蒂突然说道。这五个字在我心中回响了五十年。

**问题与证据**：保存记录证明这里存在真实初译至终译变化，实际差异为“五个字”→“句话”。保存的初译与终译存在可核对的文本变化。

**调整机制与效果**：恢复跨句回指对象或显式主语，使篇章指称链在中文中可追踪。该变化的可观察效果仅限当前文本关系；现有记录不支持对修订动机、选择过程或读者反应作历史断言。

**证据边界**：本例只支持保存的实际文本差异，不支持未记录的修订理由。

**跨案例发现**：恢复跨句回指对象或显式主语，使篇章指称链在中文中可追踪。

### 3.6.2 叙事声音与对话节奏

<!--portfolio-case:seg-ec100d8686d3891e-0083-->

**叙事声音与对话节奏（seg-ec100d8686d3891e-0083，tier_1_core）**

> [SOURCE_EXCERPT seg-ec100d8686d3891e-0083]: “I’ve got it!” he tells me immediately.

> [TARGET_EXCERPT seg-ec100d8686d3891e-0083]: “我来操纵！”他立刻告诉我。

> [REVIEW_FINDING seg-ec100d8686d3891e-0083]: “他立刻告诉我”略显平淡，原文 immediately 强调即时反应，建议改为“他立刻对我说”或“他马上告诉我”，更符合口语化叙事风格。

**问题界定**：当前译文呈现了已被审校记录指出的问题。“他立刻告诉我”略显平淡，原文 immediately 强调即时反应，建议改为“他立刻对我说”或“他马上告诉我”，更符合口语化叙事风格。

**问题机制与错误诱因**：源文表面对应关系可能掩盖语境、搭配、结构或指称上的约束；本例需要按以下机制核对：用符合人物关系和叙事速度的报告语、口语结构与节奏组织对话。

**分析性方案与预期效果**：审校记录已指出可调整的表达方向，但未保存实际采用的新译文。该方案的意义在于针对上述具体关系，而不是笼统追求“更自然”。该例记录的是审校问题和建议，不是已经发生的修订。

**证据边界**：当前项目不能证明该建议已经实施，也不能据此还原译者意图。

**跨案例发现**：用符合人物关系和叙事速度的报告语、口语结构与节奏组织对话。

### 3.6.3 反问、态度与语用力度

<!--portfolio-case:SC-0141-->

**反问、态度与语用力度（SC-0141，tier_3_contrast_boundary）**

> [SYNTHETIC_SOURCE SC-0141]: After Israel’s tenth anniversary celebrations, in the spring of 1958, he told me how he once said to Berl Katznelson, a founder of Labor Zionism: “What do you need that Ben-Gurion for?”

> [SIMULATED SC-0141]: 在1958年春天以色列建国十周年庆典之后，他告诉我有一次他对劳工锡安主义的创始人贝尔·卡茨内尔森说：“你为什么需要那个本-古里安？”

> [OPTIMIZED SC-0141]: 在1958年春天以色列建国十周年庆典之后，他告诉我有一次他对劳工锡安主义的创始人贝尔·卡茨内尔森说：“你要那个本-古里安干什么？”

该材料是分析阶段生成的受控对比，不代表作者历史初译。This rhetorical question conveys dismissiveness toward Ben-Gurion, implying he is unnecessary or problematic. The pragmatics are confrontational and colloquial. A translator may render it as a genuine information-seeking question or soften the dismissive edge, losing the political tension.

其修复机制在于：区分真实询问与反问等言语行为，保持态度、对抗性和人物刻画。本例只能说明一种可能的失败机制，不能证明人类译者的错误频率或实际读者反应。

**跨案例发现**：区分真实询问与反问等言语行为，保持态度、对抗性和人物刻画。

## 3.7 跨案例综合与研究局限

组合结果表明，局部词语选择只是问题的一层；段落对应、修饰辖域、逻辑关系、专名政策、回指链与人物语气会在不同层面共同影响译文。核心案例负责建立机制，Supporting Example用于检验同一机制在其他语境中的表现，Boundary Case 则阻止不可靠证据进入结论。

本章能证明的是保存文本之间的差异、当前译文中被审校指出的问题以及受控对比中的可能机制。它不能把审校建议当成已执行修订，不能用合成材料推断人类错误频率，也不能在缺少作者回答时声称还原了历史翻译意图。后续最高优先级是取得真实 Human Author Evidence，并为真正需要理论解释的机制登记可核验 Literature Evidence。
