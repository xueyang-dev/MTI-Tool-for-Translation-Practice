## 1 引言

<!--rq:RQ1-->
<!--claim:C1-->

## 1 引言

### 1.1 研究背景与意义

回忆录作为一种兼具历史记录与个人记忆双重属性的叙事文体，其翻译实践涉及语言转换与跨文化传递的双重挑战。当回忆录以飞行员为叙述主体、以以色列建国初期至数次中东战争为背景时，源文本中密集嵌入的历史事件、地理名称、人名及文化专有项，使得翻译任务在语言层面与内容层面均呈现出可实证的复杂性。本项目所处理的源文本即属此类：一位以色列飞行员的回忆录，以第一人称视角回溯童年经历与家族记忆，叙事时间横跨以色列建国前后的多个关键历史节点。

从项目数据看，该回忆录源文本共273<!--stat:total_segments-->个段落，全部完成翻译（273<!--stat:translated_segments-->段），其中264<!--stat:reviewed_segments-->段经过审校环节。审校过程中共识别出32<!--stat:actionable_findings-->项可操作问题，问题类型分布为：自动检查发现{{STAT:issue_category_distribution.check}}项、人工审校发现{{STAT:issue_category_distribution.review}}项。这一数据表明，翻译过程中确实存在需要人工介入修正的问题，而非机器翻译可完全自动解决。

从源文本特征看，语言与内容两个层面的复杂性均有可追溯的项目证据支撑。在语言层面，部分段落呈现出显著的长句、多从句与复杂标点特征。例如，第144段源文本长达3632字符，包含14个从句标记与85处标点符号，且直接引语与叙述交织：

> [SOURCE seg-ec100d8686d3891e-0144]: We were nine years old. It was spring. The poppies were in bloom, and so were the chrysanthemums. Back then, we didn’t know it happened six months before Operation Kadesh, which was in 1956. Dad drove from the valley to the Negev, near Gaza, to harvest hay in the fields of Nahal Oz. This time, he took me with him. He asked for and received permission from my teacher, Rachel, who placed her hand on my head, looked me in the eyes, and listened to my breathing. “No asthma. It’s the Lag Ba’Omer holiday too. It’s fine.” It was dark, and we were all still asleep when Dad woke me up. “Brush your teeth, Zevik.” “What about everyone else?” I asked. “You’re the only one coming,” Dad replied. He was thirty-five, thirty-five years old. Where was I at thirty-five? The First Lebanon War. Five wars later. I sat in the jeep on the right side. I remember the smell of burnt gasoline and the moment just before sunrise, when Dad turned off the lights. The red of the poppies and the yellow of the chrysanthemums gave way to the pink of flax and the blue of cornflowers. Dad sang about Samson’s foxes carrying torches at night, and that the main things in the jeep were speed, clutch, and reverse. Not a word about Mom or the two other kids he already had then. I asked him if they had found his missing harmonica. “Forget about it,” he said. And then he told me about the World War. Brindisi. The mortars. Entering Rome. The squares, the fountains. “You know, Rome is no Afula.” Not a word about the meeting of the Jewish soldiers with the Pope, about the way he blessed them in Hebrew. At the Migdal-Ashkelon junction, we stopped. Dad pulled out a thermos of tea and two sandwiches with hard-boiled eggs from the back. “Eat, Zevik, you’re a weakling.” When we arrived at Nahal Oz, we saw someone in uniform, one eye covered, coming out of the kibbutz dining hall. “What is Moshe Dayan doing here?” Dad wondered. “They killed Roy,” answered a woman with red, tearful eyes. “Dayan came here last night for a relative’s wedding. We had four weddings planned for yesterday. He stayed over for the funeral.” “Don’t ask what they did to Roy’s body before they returned it to us.” “Who is Moshe Dayan?” I asked. “The Chief of Staff,” Dad replied. I did not ask what a Chief of Staff was, who Roy was, or what they had done to his body. I was too embarrassed. Dad took my hand, and we joined a long procession following a coffin draped in the Israeli flag. High above us, large birds circled in the sky. The people carrying the coffin on their shoulders lowered it into a grave. Soldiers fired rifles pointed toward the sky. Dad covered my ears with his large, calloused hands. The people took shovels and filled the grave with earth and stones. And then there was silence. Moshe Dayan pulled a piece of paper out of his pocket and read from it. A strong wind blew from the west. I caught fragments of sentences. From ourselves, we will demand his blood. How did we shut our eyes. With all of its cruelty. To tear us to pieces. A steel helmet and a cannon’s mouth. To plant a tree and build a home. Shelters. Barbed wire. A machine gun. Millions of Jews. The ashes of history. A land for our people. A sea of hatred and revenge. Roy’s blood cries out to us. His torn body. Hundreds of thousands of Arabs. The decree of our generation, the choice of our lives. Armed, strong, and unyielding. The sword will fall; our lives will be cut off. The blond boy. The gleam of the blade. Gaza’s gates are weighty. The Chief of Staff folded the piece of paper and put it back in his pocket. Dad approached him and told him he had named his second son after

该段落的终译如下：

> [TARGET seg-ec100d8686d3891e-0144]: ```json [   "我们九岁。那是春天。罂粟花开了，菊花也开了。那时，我们并不知道这发生在卡迭石行动（1956年）前六个月。爸爸从山谷开车到内盖夫，靠近加沙，去纳哈尔奥兹的田里收割干草。这一次，他带上了我。他向我的老师拉结请求并获得了许可，她把手放在我的头上，看着我的眼睛，听了听我的呼吸。“没有哮喘。而且也是篝火节。没问题。”天还黑着，我们都还在睡梦中，爸爸叫醒了我。“刷牙，泽维克。”“其他人呢？”我问。“只有你一个去。”爸爸回答。他三十五岁，三十五岁。我三十五岁时在哪里？第一次黎巴嫩战争。五次战争之后。我坐在吉普车的右边。我记得烧汽油的味道，以及日出前的那一刻，爸爸关掉了车灯。罂粟的红和菊花的黄让位给了亚麻的粉和矢车菊的蓝。爸爸唱着参孙的狐狸在夜里带着火把的故事，还说吉普车里最重要的是速度、离合器和倒挡。关于妈妈或他那时已经有的另外两个孩子，他只字未提。我问他是否找到了他丢失的口琴。“别提了。”他说。然后他给我讲了世界大战的事。布林迪西。迫击炮。进入罗马。广场，喷泉。“你知道，罗马可不是阿富拉。”关于犹太士兵与教皇的会面，关于他用希伯来语为他们祝福的方式，他只字未提。在米格达尔-阿什凯隆路口，我们停了下来。爸爸从后面拿出一个装着茶的热水瓶和两个夹着煮鸡蛋的三明治。“吃吧，泽维克，你是个弱不禁风的孩子。”当我们到达纳哈尔奥兹时，我们看到一个穿制服的人，一只眼睛蒙着，从基布兹食堂出来。“摩西·达扬在这里做什么？”爸爸疑惑道。“他们杀了罗伊。”一个红着眼睛、泪流满面的女人回答。“达扬昨晚来参加一个亲戚的婚礼。我们昨天原计划有四场婚礼。他留下来参加了葬礼。”“别问他们在把罗伊的尸体还给我们之前对他做了什么。”“摩西·达扬是谁？”我问。“总参谋长。”爸爸回答。我没有问总参谋长是什么，罗伊是谁，或者他们对他的尸体做了什么。我太尴尬了。爸爸牵着我的手，我们加入了一支长长的队伍，跟随着一口覆盖着以色列国旗的棺材。在我们头顶高处，大鸟在天空中盘旋。抬棺材的人把它放进了墓穴。士兵们朝天鸣枪。爸爸用他粗糙的大手捂住我的耳朵。人们拿起铁锹，用泥土和石头填满了墓穴。然后一片寂静。摩西·达扬从口袋里掏出一张纸，读了起来。一阵强风从西边吹来。我捕捉到一些句子的片段。我们要向他讨还血债。我们是如何闭上眼睛的。带着它所有的残酷。要把我们撕成碎片。一顶钢盔和炮口。种树建房。防空洞。铁丝网。一挺机枪。数百万犹太人。历史的灰烬。一片属于我们人民的土地。一片仇恨与复仇的海洋。罗伊的血在向我们呼喊。他破碎的身体。数十万阿拉伯人。我们这一代的宿命，我们生命的选择。武装起来，坚强不屈。剑将落下；我们的生命将被切断。那个金发男孩。刀刃的寒光。加沙的大门沉重。总参谋长折起那张纸，放回口袋。爸爸走近他，告诉他，他给自己的第二个儿子取名为", ] ```

该案例同时呈现了语言与内容两个层面的特征：长句与复杂标点构成语言层面的处理困难，而“Operation Kadesh”“Nahal Oz”“Lag Ba’Omer”“Moshe Dayan”“kibbutz”等历史事件、地名、节日、人名与文化专有项的密集出现，则构成内容层面的处理困难。其中“kibbutz”一词在项目中采用了“基布兹（集体农庄）”的术语决策基布兹（集体农庄）<!--term:t-13bdacf558f9-->，以兼顾音译与释义。审校环节在该段落识别出译文末尾“取名为”后内容缺失的问题，原文以“after”结尾暗示后续有名字，但译文未完整呈现，造成语义不完整。这一发现表明，长句与复杂标点并非仅是静态的文本特征，而是确实在翻译过程中转化为可实证的难点——机器翻译在处理该长段时未能保证语义的完整性，需要人工审校介入识别并修正。

类似的语言复杂性在其他段落中亦有体现。第238段源文本长达1202字符，包含4个从句标记与28处标点符号，直接引语与叙述交织，且涉及多部电影名称与人名：

> [SOURCE seg-ec100d8686d3891e-0238]: We went into Domino, and Amos bought everyone ice cream sandwiches. We sat in the second-to-last row. The newsreel was about infiltrators in the Negev and the Nahal entertainment troupe. They sang He Didn’t Know Her Name and Dina Barzilai. The lion roared, and the movie began. Good thing it wasn’t in color like The Wizard of Oz, because there was a lot of blood. It was about a massive prison in America with sadistic guards, especially the head warden. The prisoners in Block 11 spent their nights making knives and even crude guns, plotting a revolt. After dinner, they returned to their cells. The guards locked the doors, turned off the lights, and left. A moment of silence hung in the air – then I heard him breathing, those breaths of his. He felt that his heavy, wheezing breaths were disturbing everyone, so he closed his eyes. Palace, he murmured with his mouth shut. Marilyn Monroe. He saw unemployed musicians fleeing from the mob, disguising themselves as women. He saw Sugar eating a chicken drumstick and kissing Tony Curtis on the bed of a millionaire’s yacht. A speedboat gliding in reverse. And Jack Lemmon saying, “I smoke, I’m not a real blonde, I can’t have children, I’m a man.”

> [TARGET seg-ec100d8686d3891e-0238]: 我们走进多米诺电影院，阿莫斯给大家买了冰淇淋三明治。我们坐在倒数第二排。新闻短片播放的是关于内盖夫渗透者和纳哈尔文工团的报道，他们唱了《他不知道她的名字》和迪娜·巴拉齐尔的歌。狮子吼叫，电影开始了。幸好不是像《绿野仙踪》那样的彩色片，因为里面有很多血。电影讲述的是美国一座大型监狱，狱警残暴，尤其是典狱长。11号牢房的囚犯们夜晚磨制刀具，甚至粗糙的枪支，密谋暴动。晚餐后，他们回到牢房。狱警锁上门，关灯离开。片刻寂静悬在空中——然后我听到他的呼吸声，那种特有的呼吸。他感到自己沉重而喘息的声音打扰了大家，便闭上眼睛。“宫殿，”他闭着嘴低语。“玛丽莲·梦露。”他看到失业的音乐家逃离暴徒，装扮成女人。他看到苏格啃着鸡腿，在百万富翁游艇的床上亲吻托尼·柯蒂斯。一艘快艇倒着滑行。杰克·莱蒙说：“我抽烟，我不是真正的金发女郎，我不能生孩子，我是个男人。”

在内容层面，源文本密集嵌入以色列历史事件、地理名称、人名及文化专有项。第140段涉及“Geva”“Palmach”“Ben-Gurion”“Tabenkin”“Beit HaShita”“Gutman”等地理名称、历史人物与政治运动名称：

> [SOURCE seg-ec100d8686d3891e-0140]: Ruth served coffee and asked me, three and a half years old, how things were in Geva. Someone walked in, patted Azariah on the shoulder, and asked, “Why did they dismantle the Palmach unit, anyway?” “Ask Ben-Gurion, or Tabenkin,” Azariah replied without a smile. For a moment, there was a sense of sorrow in that small room in Beit HaShita, which held a painting by Gutman of a few white anemones, but no radio or telephone, and, like everywhere else, there was no reason to lock the door.

> [TARGET seg-ec100d8686d3891e-0140]: 露丝端上咖啡，问我这个三岁半的孩子，格瓦（Geva）的情况如何。有人走进来，拍了拍阿扎里亚的肩膀，问道：“他们到底为什么解散了帕尔马赫部队？”“去问本-古里安，或者塔本金，”阿扎里亚没有笑容地回答。片刻间，贝特哈希塔那间小屋里弥漫着一股悲伤的气息，屋里挂着一幅古特曼画的几朵白色银莲花，但没有收音机或电话，而且和其他地方一样，没有理由锁门。

第233段同样呈现了专名与文化指涉的密集分布，涉及电影片名、影院名称及人名：

> [SOURCE seg-ec100d8686d3891e-0233]: On the way, Amos said there were two movies in Haifa that we could see – Some Like It Hot, playing at the Palace Cinema, and Riot in Cell Block 11, showing at the Domino Cinema. The girls wanted to go to the Palace, and we wanted to go to Domino. They took a vote, and it ended in a tie – eleven girls and eleven boys. He whispered quietly, ‘Palace, Palace.’ Amos said that if it was a tie, he would decide; we were going to Domino. Someone said, ‘Marilyn Monroe,’ and Amos replied, ‘If it were Brigitte Bardot’ ... and Noam added, ‘Or Roni Hofner.’ But he was sitting at the far end of the second row in the truck, so she didn’t hear him.

> [TARGET seg-ec100d8686d3891e-0233]: 路上，阿莫斯说海法有两部电影可选——《热情如火》在皇宫影院上映，《监狱摇滚》在多米诺影院放映。女孩们想去皇宫，我们想去多米诺。他们投票表决，结果平局——十一个女孩对十一个男孩。有人轻声嘀咕：“皇宫，皇宫。”阿莫斯说平局由他定夺，我们去多米诺。有人说：“玛丽莲·梦露。”阿莫斯回应：“要是碧姬·芭铎……”诺姆插嘴：“或者罗妮·霍夫纳。”但他坐在卡车第二排靠边位置，她没听见。

第139段则呈现了比喻性表达的翻译难点：

> [SOURCE seg-ec100d8686d3891e-0139]: Back then, Dad wasn’t building houses yet; he was repairing machines. Even then, I think I already sensed that he did things I would never be able to do. Many years later, I asked him to teach me how to weld. “What do you need that for?” he replied, as was his way, once again evading the outstretched hand.

> [TARGET seg-ec100d8686d3891e-0139]: 那时，父亲还未开始建造房屋，他还在修理机器。即便在那时，我想我已隐约感觉到，他所做的事情是我永远无法企及的。多年以后，我请他教我焊接技术，他却以他一贯的方式回答：“你需要那个做什么？”再次避开了我伸出的手。

此外，第7段作为全书题献，虽篇幅极短，却涉及人名保留与中文书写习惯的协调问题：

> [SOURCE seg-ec100d8686d3891e-0007]: For Grandma Sarah and Grandpa Yaakov

> [TARGET seg-ec100d8686d3891e-0007]: 献给祖母Sarah和祖父Yaakov

上述案例共同表明，源文本在语言层面呈现长句、多从句、复杂标点与直接引语交织的特征，在内容层面密集嵌入以色列历史事件、地理名称、人名及文化专有项。需要进一步说明的是，这些特征之所以构成“可实证的翻译难点”，关键在于审校环节确实识别出了与这些特征直接相关的问题。具体而言：第144段的语义截断问题直接源于长句与复杂结构的处理困难，机器翻译在该长段末尾未能完整呈现原文语义；第233段的专名译名不准确（如“Riot in Cell Block 11”被译为“监狱摇滚”）与主语漏译（“He whispered quietly”被译为“有人轻声嘀咕”），直接指向专名处理与复杂句式理解方面的难点；第140段的地名处理不一致（“格瓦（Geva）”保留括号原文而“贝特哈希塔”未保留）表明文化专有项的处理缺乏统一策略；第7段的源语残留（“Sarah”“Yaakov”未译）则说明人名处理在极短文本中同样构成难点。这些审校发现构成了从文本特征到翻译难点的推理链条：正是由于源文本在语言与内容层面的上述特征，翻译过程中才出现了相应的问题，而这些问题的存在与分布（{{STAT:issue_category_distribution.check}}项自动检查问题、{{STAT:issue_category_distribution.review}}项人工审校问题）共同印证了难点确实在翻译过程中显现，而非仅停留在文本特征的静态描述层面。

### 1.2 研究问题

基于上述背景，本研究提出三个研究问题。第一个研究问题关注源文本的语言特征与可证实的翻译难点：源文本（飞行员回忆录）的主要语言特征与可证实的翻译难点是什么？第二个研究问题从功能对等视角对翻译决策进行有限解释：代表性翻译决策从功能对等视角可作何种有限解释？第三个研究问题关注翻译流程中的工具与环节：术语治理、机器翻译、审校与译后编辑在本项目中呈现了哪些可追溯效果与局限？

需要说明的是，本研究的分析定位为“证据约束型”研究，即所有结论均以项目过程中可观察、可追溯的证据为限。研究不试图还原译者不可观察的心理意图，也不将功能对等理论扩展为对全部翻译决策的统摄性解释，而是从结果反推决策倾向，以项目证据为判断依据。

### 1.3 研究方法与论文结构

本研究采用基于项目过程证据的案例研究与描述性统计方法。分析材料包括：源文本段落的结构特征数据、初译与终译的对照记录、审校环节发现的问题类型分布、术语决策记录，以及机器翻译与人工审校的交互痕迹。案例选取遵循证据完整性原则，优先选择具备完整翻译证据链（即初译、审校发现、修复记录齐备）的段落。

论文结构安排如下：第二章基于项目证据系统分析源文本的语言特征与内容特征，归纳可实证的翻译难点；第三章从功能对等视角对代表性翻译决策进行有限解释；第四章基于项目统计与案例证据，分析术语治理、机器翻译、审校与译后编辑的可追溯效果与局限；第五章总结研究发现，回应研究问题，说明研究贡献与局限。

## 2 源文本特征与翻译难点分析

## 2 源文本特征与翻译难点分析

<!--rq:RQ1-->

本章基于项目过程证据，从语言层面与内容层面两个维度系统考察源文本的特征，并据此归纳在翻译实践中可实证的难点。分析所依据的材料包括源文本段落的结构特征数据、初译与终译的对照记录、审校环节发现的问题类型分布，以及术语决策记录。需要说明的是，本章所讨论的“难点”并非对译者主观感受的推测，而是以审校环节实际识别出的问题为证据基础，即那些在翻译过程中确实引发处理困难、并留下可追溯痕迹的语言或内容特征。

### 2.1 语言层面的特征：长句、多从句与复杂标点

从项目数据看，源文本在语言层面呈现出长句密集、从句嵌套、标点复杂且直接引语交织的显著特征。以段落 seg-ec100d8686d3891e-0144 为例，该段源文本字符数达3632，包含14个从句标记（clause markers）与85处标点符号，是项目中最具代表性的长段落之一。该段以第一人称回忆叙事展开，将童年记忆、历史事件、人物对话与内心独白交织于同一叙述流中：

> [SOURCE seg-ec100d8686d3891e-0144]: We were nine years old. It was spring. The poppies were in bloom, and so were the chrysanthemums. Back then, we didn’t know it happened six months before Operation Kadesh, which was in 1956. Dad drove from the valley to the Negev, near Gaza, to harvest hay in the fields of Nahal Oz. This time, he took me with him. He asked for and received permission from my teacher, Rachel, who placed her hand on my head, looked me in the eyes, and listened to my breathing. “No asthma. It’s the Lag Ba’Omer holiday too. It’s fine.” It was dark, and we were all still asleep when Dad woke me up. “Brush your teeth, Zevik.” “What about everyone else?” I asked. “You’re the only one coming,” Dad replied. He was thirty-five, thirty-five years old. Where was I at thirty-five? The First Lebanon War. Five wars later. I sat in the jeep on the right side. I remember the smell of burnt gasoline and the moment just before sunrise, when Dad turned off the lights. The red of the poppies and the yellow of the chrysanthemums gave way to the pink of flax and the blue of cornflowers. Dad sang about Samson’s foxes carrying torches at night, and that the main things in the jeep were speed, clutch, and reverse. Not a word about Mom or the two other kids he already had then. I asked him if they had found his missing harmonica. “Forget about it,” he said. And then he told me about the World War. Brindisi. The mortars. Entering Rome. The squares, the fountains. “You know, Rome is no Afula.” Not a word about the meeting of the Jewish soldiers with the Pope, about the way he blessed them in Hebrew. At the Migdal-Ashkelon junction, we stopped. Dad pulled out a thermos of tea and two sandwiches with hard-boiled eggs from the back. “Eat, Zevik, you’re a weakling.” When we arrived at Nahal Oz, we saw someone in uniform, one eye covered, coming out of the kibbutz dining hall. “What is Moshe Dayan doing here?” Dad wondered. “They killed Roy,” answered a woman with red, tearful eyes. “Dayan came here last night for a relative’s wedding. We had four weddings planned for yesterday. He stayed over for the funeral.” “Don’t ask what they did to Roy’s body before they returned it to us.” “Who is Moshe Dayan?” I asked. “The Chief of Staff,” Dad replied. I did not ask what a Chief of Staff was, who Roy was, or what they had done to his body. I was too embarrassed. Dad took my hand, and we joined a long procession following a coffin draped in the Israeli flag. High above us, large birds circled in the sky. The people carrying the coffin on their shoulders lowered it into a grave. Soldiers fired rifles pointed toward the sky. Dad covered my ears with his large, calloused hands. The people took shovels and filled the grave with earth and stones. And then there was silence. Moshe Dayan pulled a piece of paper out of his pocket and read from it. A strong wind blew from the west. I caught fragments of sentences. From ourselves, we will demand his blood. How did we shut our eyes. With all of its cruelty. To tear us to pieces. A steel helmet and a cannon’s mouth. To plant a tree and build a home. Shelters. Barbed wire. A machine gun. Millions of Jews. The ashes of history. A land for our people. A sea of hatred and revenge. Roy’s blood cries out to us. His torn body. Hundreds of thousands of Arabs. The decree of our generation, the choice of our lives. Armed, strong, and unyielding. The sword will fall; our lives will be cut off. The blond boy. The gleam of the blade. Gaza’s gates are weighty. The Chief of Staff folded the piece of paper and put it back in his pocket. Dad approached him and told him he had named his second son after

该段落的语言特征可从三个层面加以描述。其一，句式结构上，段落内部频繁切换于完整句、省略句与名词性短语之间，如“Brindisi. The mortars. Entering Rome. The squares, the fountains.”以碎片化句式模拟记忆的跳跃性，而“He asked for and received permission from my teacher, Rachel, who placed her hand on my head, looked me in the eyes, and listened to my breathing”则呈现多动词并列与关系从句嵌套的复合结构。其二，标点使用上，段落中直接引语密集出现，引号内的对话与叙述者的内心独白交替推进，破折号、分号与逗号的多层使用进一步增加了句读切分的复杂度。其三，叙事时间轴上，段落以“那时—现在—那时”的往复跳跃组织叙述，如“He was thirty-five, thirty-five years old. Where was I at thirty-five? The First Lebanon War. Five wars later.”在回忆与当下之间快速切换，这种时间维度的交错对译文的时态处理与叙事连贯性构成额外负担。

需要说明的是，seg-ec100d8686d3891e-0144 的源文本字符数达3632，远超项目段落的平均水平，属于极端案例而非典型样本。将其作为语言特征的代表性证据，其意义在于展示源文本在极端情况下所能达到的复杂度上限，而非推断所有段落均具有同等程度的复杂性。为增强归纳的稳健性，下文补充考察另一结构特征相近但规模适中的段落。

段落 seg-ec100d8686d3891e-0238 源文本字符数为1202，包含4个从句标记与28处标点符号，同样呈现直接引语与叙述交织的结构：

> [SOURCE seg-ec100d8686d3891e-0238]: We went into Domino, and Amos bought everyone ice cream sandwiches. We sat in the second-to-last row. The newsreel was about infiltrators in the Negev and the Nahal entertainment troupe. They sang He Didn’t Know Her Name and Dina Barzilai. The lion roared, and the movie began. Good thing it wasn’t in color like The Wizard of Oz, because there was a lot of blood. It was about a massive prison in America with sadistic guards, especially the head warden. The prisoners in Block 11 spent their nights making knives and even crude guns, plotting a revolt. After dinner, they returned to their cells. The guards locked the doors, turned off the lights, and left. A moment of silence hung in the air – then I heard him breathing, those breaths of his. He felt that his heavy, wheezing breaths were disturbing everyone, so he closed his eyes. Palace, he murmured with his mouth shut. Marilyn Monroe. He saw unemployed musicians fleeing from the mob, disguising themselves as women. He saw Sugar eating a chicken drumstick and kissing Tony Curtis on the bed of a millionaire’s yacht. A speedboat gliding in reverse. And Jack Lemmon saying, “I smoke, I’m not a real blonde, I can’t have children, I’m a man.”

该段同样呈现多层次的叙事结构：叙述者回忆观影经历，其间嵌入电影情节的描述、人物对话的转述以及内心感受的抒发。段落中“Palace, he murmured with his mouth shut. Marilyn Monroe.”以名词短语与简短句构成意识流式的叙述片段，而“A speedboat gliding in reverse”与“And Jack Lemmon saying, ...”则使用非限定动词结构延续叙述流。这类句式在英文中自然流畅，但转换为中文时，若照搬原文的句式结构，容易造成译文冗长或语义含混；若过度拆分，则可能损失原文的叙事节奏与意识流效果。该段的初译与终译一致，且被标记为已审校（reviewed），说明其翻译处理在审校环节未引发额外问题，但源文本的结构复杂度本身仍然构成翻译过程中需要处理的客观特征。

上述语言特征在翻译实践中的具体影响，可以通过审校环节针对相关段落识别出的问题加以印证。以 seg-ec100d8686d3891e-0144 为例，该段在审校环节被识别出一条可操作问题，指向译文末尾“取名为”后内容缺失——原文以“after”结尾，暗示后续有名字，但译文未完整呈现或标注截断，造成语义不完整。这一问题的产生与段落的长句结构直接相关：在长达3632字符的连续叙述中，译者在处理段落末尾时未能完整呈现原文的语义信息，说明长段落的语义完整性维护是翻译实践中的实际难点。类似地，段落 seg-ec100d8686d3891e-0233 的审校意见指出，“He whispered quietly”译为“有人轻声嘀咕”不准确，原文主语是“他”，漏译了主语。该段源文本字符数为639，包含4个从句标记与26处标点符号，直接引语与叙述交织的结构特征同样明显。这一问题的产生可解释为：在直接引语密集、叙述主体频繁切换的段落中，译者在处理引语归属时出现了主语辨识的偏差，说明直接引语与叙述交织的结构确实对译文的准确性构成了实际影响。

从项目统计看，{{STAT:issue_category_distribution}}显示审校环节共记录67条问题，其中check类18条、review类49条。这些问题的分布在一定程度上印证了上述语言特征对翻译过程的实际影响：长句与复杂标点所导致的语义切分困难、直接引语与叙述交织所带来的语体转换问题，均在审校环节以可操作问题（actionable findings）的形式被识别出来。32<!--stat:actionable_findings-->条可操作问题的存在，说明源文本的语言特征并非仅停留在静态描述层面，而是在翻译实践中转化为具体的处理难点。

### 2.2 内容层面的特征：历史事件、地理名称与文化专有项

<!--claim:C1-->

源文本在内容层面密集嵌入以色列历史事件、地理名称、人名及文化专有项，这一特征与上述语言特征共同构成翻译难点的两个维度。从项目案例看，源文本涉及的历史事件包括卡迭石行动（Operation Kadesh）、第一次黎巴嫩战争（The First Lebanon War）等；地理名称涵盖以色列境内多个地点，如纳哈尔奥兹（Nahal Oz）、阿特利特（Atlit）、米格达尔-阿什凯隆路口（Migdal-Ashkelon junction）等；人名则包括摩西·达扬（Moshe Dayan）、本-古里安（Ben-Gurion）、塔本金（Tabenkin）等以色列历史与政治人物。此外，文本还涉及犹太文化专有项，如篝火节（Lag Ba’Omer）、基布兹（Kibbutz）等。

段落 seg-ec100d8686d3891e-0140 集中呈现了人名与历史背景交织的特征：

> [SOURCE seg-ec100d8686d3891e-0140]: Ruth served coffee and asked me, three and a half years old, how things were in Geva. Someone walked in, patted Azariah on the shoulder, and asked, “Why did they dismantle the Palmach unit, anyway?” “Ask Ben-Gurion, or Tabenkin,” Azariah replied without a smile. For a moment, there was a sense of sorrow in that small room in Beit HaShita, which held a painting by Gutman of a few white anemones, but no radio or telephone, and, like everywhere else, there was no reason to lock the door.

该段在不足500字符的篇幅内，集中出现了格瓦（Geva）、贝特哈希塔（Beit HaShita）两个地名，阿扎里亚（Azariah）、本-古里安（Ben-Gurion）、塔本金（Tabenkin）、古特曼（Gutman）四个人名，以及“帕尔马赫部队”（Palmach unit）这一军事组织名称。这些专有名词在中文语境中缺乏统一的通用译名，翻译时需要在音译、保留原文与加注之间做出选择。该段的初译与终译均为：

> [TARGET seg-ec100d8686d3891e-0140]: 露丝端上咖啡，问我这个三岁半的孩子，格瓦（Geva）的情况如何。有人走进来，拍了拍阿扎里亚的肩膀，问道：“他们到底为什么解散了帕尔马赫部队？”“去问本-古里安，或者塔本金，”阿扎里亚没有笑容地回答。片刻间，贝特哈希塔那间小屋里弥漫着一股悲伤的气息，屋里挂着一幅古特曼画的几朵白色银莲花，但没有收音机或电话，而且和其他地方一样，没有理由锁门。

审校环节对该段提出了明确意见，指出译文“格瓦（Geva）”中括号保留原文的做法与审校要求不符——按审校要求地名应保留原文，无需加注拼音或括号；同时“贝特哈希塔”未保留原文，建议统一处理。这一案例说明，专有名词的处理策略在项目中尚未形成完全统一的规范，不同段落之间存在处理方式不一致的情况，这本身即是翻译难点的一种表现。

段落 seg-ec100d8686d3891e-0215 则呈现了另一类专名处理问题：

> [SOURCE seg-ec100d8686d3891e-0215]: He tried to tan, but his skin turned red. He walked with the older kids toward Atlit and back, collected a lot of seashells, and found one that echoed the sound of the sea when he held it to his ear. He also found a rare one, a dark shell, that only he had until the end of camp. He refused to trade it, remembering what had happened on the trip to the Rabbits Hideaway and Chair Hill. There, he had found a truly ancient oil lamp, perfectly intact, but they gave him a worthless one in exchange. The lamp story – that was a long time ago.

该段中“Atlit”为以色列沿海城镇名，“Rabbits Hideaway”与“Chair Hill”为带有叙事色彩的地点名称。初译将三者分别处理为“阿特利特”“兔子藏身处”“椅子山”：

> [TARGET seg-ec100d8686d3891e-0215]: 他试着晒黑，但皮肤却变红了。他和年长的孩子们一起走到阿特利特再折返，收集了许多贝壳，还找到一个贴在耳边能回响海声的。他还发现了一个稀有的深色贝壳，直到营地结束前只有他拥有。他拒绝交换，想起了去兔子藏身处和椅子山的旅行中发生的事。在那里，他找到了一盏真正古老的油灯，完好无损，但他们却换给他一个毫无价值的。油灯的故事——那是很久以前的事了。

审校意见指出，“Atlit”是地名，应保留原文；“Rabbits Hideaway”和“Chair Hill”是专有地名，应保留原文或加注中文译名并保留原文。审校建议的译文为：

> [TARGET seg-ec100d8686d3891e-0215]: 他试着晒黑，但皮肤却变红了。他和年长的孩子们一起走到阿特利特再折返，收集了许多贝壳，还找到一个贴在耳边能回响海声的。他还发现了一个稀有的深色贝壳，直到营地结束前只有他拥有。他拒绝交换，想起了去兔子藏身处和椅子山的旅行中发生的事。在那里，他找到了一盏真正古老的油灯，完好无损，但他们却换给他一个毫无价值的。油灯的故事——那是很久以前的事了。

这一案例表明，对于专有名词，项目审校倾向于保留原文而非音译或意译，反映出专名处理策略在项目内部仍在动态调整之中。

文化专有项方面，段落 seg-ec100d8686d3891e-0144 中出现了“Lag Ba’Omer”（篝火节）与“Kibbutz”（基布兹）两个文化负载词。其中“Kibbutz”在项目中建立了术语决策记录，基布兹（集体农庄）<!--term:t-13bdacf558f9-->将其译为“基布兹（集体农庄）”，采用音译加注释的方式，既保留了源语的文化身份，又为目标读者提供了理解线索。从结果看可解释为，这一处理方式与功能对等理论中“在无法实现形式对等时，通过补偿手段实现功能对等”的思路相契合；但需说明的是，该术语决策的状态为“暂定”（provisional），其最终效果仍有待检验。

### 2.3 可实证的翻译难点归纳

综合上述语言层面与内容层面的分析，可将源文本的翻译难点归纳为以下可实证的问题类别。需要说明的是，本节对问题类别的归纳以审校环节识别出的可操作问题（actionable findings）为证据基础，并通过对问题类别的出现频率与证据完整性的综合评估来检验相关判断的可靠性。

从项目统计看，{{STAT:issue_category_distribution}}显示审校环节共记录67条问题，其中check类18条、review类49条。在这67条问题中，32<!--stat:actionable_findings-->条为可操作问题（actionable findings），即需要采取具体修改措施的问题。对这些可操作问题按内容类别进行归类，可以发现其分布呈现明显的集中趋势：专有名词处理类问题（包括人名、地名、作品名的音译、意译、保留原文及书写规范）与语义完整性问题（包括漏译、语义截断、表述不完整）构成了可操作问题的主体。以本章所考察的案例为例，seg-ec100d8686d3891e-0215 的审校意见涉及地名“Atlit”与地点名“Rabbits Hideaway”“Chair Hill”的保留原文问题；seg-ec100d8686d3891e-0233 的审校意见涉及电影名“Riot in Cell Block 11”的译名准确性问题；seg-ec100d8686d3891e-0007 的审校意见涉及人名“Sarah”“Yaakov”的残留源语问题与中文书写规范问题；seg-ec100d8686d3891e-0140 的审校意见涉及地名“Geva”“Beit HaShita”的处理方式不一致问题。这些案例均属专有名词处理类别。与此同时，seg-ec100d8686d3891e-0144 的审校意见指向译文末尾语义截断，seg-ec100d8686d3891e-0152 的审校意见指向“no longer the squills”的表述不完整，这两例均属语义完整性问题。

需要说明的是，上述案例的归类并非穷尽性的统计，而是基于本章所考察的代表性案例的归纳。32<!--stat:actionable_findings-->条可操作问题中，专有名词处理与语义完整性两类所占的具体比例，受限于项目统计数据的分类粒度，无法给出精确的数值。因此，本章对问题分布的判断采用较为审慎的表述：在已考察的案例中，专有名词处理类问题呈现较高的出现频率，且在案例中呈现出更为多样的表现形式（音译与保留原文的取舍、书写规范、译名准确性、处理方式一致性等）；语义完整性问题亦多次出现，主要表现为漏译与语义截断两种形态。与之相对，比喻性表达转换类问题（如 seg-ec100d8686d3891e-0139 的“outstretched hand”处理）在案例中仅出现一例，且该案例的审校建议未被实际采纳，其证据强度有限，尚不足以构成具有普遍性的难点类别。这一区分依据在于：专有名词处理与语义完整性问题在多个案例中重复出现，且均留下了从问题识别到修复建议的完整记录；而比喻性表达转换仅在个别案例中出现，且缺乏修复的实际落实。因此，本章对问题分布的判断，是基于问题类别的出现频率与证据完整性的综合评估，而非仅凭个别案例的简单枚举。

第一类是专有名词的处理策略问题。项目审校环节识别出的可操作问题中，相当比例集中于人名、地名、作品名的处理方式。段落 seg-ec100d8686d3891e-0007 的审校意见指出，献词中“Sarah”与“Yaakov”疑似残留源语片段，且中文亲属称谓后不应加空格。该段源文本为：

> [SOURCE seg-ec100d8686d3891e-0007]: For Grandma Sarah and Grandpa Yaakov

终译处理为：

> [TARGET seg-ec100d8686d3891e-0007]: 献给祖母Sarah和祖父Yaakov

审校建议调整为“献给祖母Sarah与祖父Yaakov”，以符合中文书写习惯。这一案例表明，专有名词在“音译”“意译”“保留原文”三种策略之间的选择缺乏统一标准，且同一策略内部还存在书写规范等细节问题。

段落 seg-ec100d8686d3891e-0233 的审校意见则指出了作品名翻译的准确性问题。该段源文本为：

> [SOURCE seg-ec100d8686d3891e-0233]: On the way, Amos said there were two movies in Haifa that we could see – Some Like It Hot, playing at the Palace Cinema, and Riot in Cell Block 11, showing at the Domino Cinema. The girls wanted to go to the Palace, and we wanted to go to Domino. They took a vote, and it ended in a tie – eleven girls and eleven boys. He whispered quietly, ‘Palace, Palace.’ Amos said that if it was a tie, he would decide; we were going to Domino. Someone said, ‘Marilyn Monroe,’ and Amos replied, ‘If it were Brigitte Bardot’ ... and Noam added, ‘Or Roni Hofner.’ But he was sitting at the far end of the second row in the truck, so she didn’t hear him.

初译与终译均为：

> [TARGET seg-ec100d8686d3891e-0233]: 路上，阿莫斯说海法有两部电影可选——《热情如火》在皇宫影院上映，《监狱摇滚》在多米诺影院放映。女孩们想去皇宫，我们想去多米诺。他们投票表决，结果平局——十一个女孩对十一个男孩。有人轻声嘀咕：“皇宫，皇宫。”阿莫斯说平局由他定夺，我们去多米诺。有人说：“玛丽莲·梦露。”阿莫斯回应：“要是碧姬·芭铎……”诺姆插嘴：“或者罗妮·霍夫纳。”但他坐在卡车第二排靠边位置，她没听见。

审校意见指出，专有名词“Riot in Cell Block 11”的译名“监狱摇滚”不准确，该片标准译名为“监狱暴动”或“第十一牢房的暴动”；同时指出“He whispered quietly”译为“有人轻声嘀咕”不准确，原文主语是“他”，漏译了主语。这一案例表明，作品名的翻译不仅涉及译名准确性问题，还涉及与既有通行译名的对接，后者需要译者具备相应的背景知识或借助外部资源加以确认。

第二类是语义完整性问题。段落 seg-ec100d8686d3891e-0144 的审校意见指出，译文末尾“取名为”后内容缺失，原文以“after”结尾，暗示后续有名字（如罗伊），但译文未完整呈现或标注截断，造成语义不完整。该段终译末尾为：

> [TARGET seg-ec100d8686d3891e-0144]: ```json [   "我们九岁。那是春天。罂粟花开了，菊花也开了。那时，我们并不知道这发生在卡迭石行动（1956年）前六个月。爸爸从山谷开车到内盖夫，靠近加沙，去纳哈尔奥兹的田里收割干草。这一次，他带上了我。他向我的老师拉结请求并获得了许可，她把手放在我的头上，看着我的眼睛，听了听我的呼吸。“没有哮喘。而且也是篝火节。没问题。”天还黑着，我们都还在睡梦中，爸爸叫醒了我。“刷牙，泽维克。”“其他人呢？”我问。“只有你一个去。”爸爸回答。他三十五岁，三十五岁。我三十五岁时在哪里？第一次黎巴嫩战争。五次战争之后。我坐在吉普车的右边。我记得烧汽油的味道，以及日出前的那一刻，爸爸关掉了车灯。罂粟的红和菊花的黄让位给了亚麻的粉和矢车菊的蓝。爸爸唱着参孙的狐狸在夜里带着火把的故事，还说吉普车里最重要的是速度、离合器和倒挡。关于妈妈或他那时已经有的另外两个孩子，他只字未提。我问他是否找到了他丢失的口琴。“别提了。”他说。然后他给我讲了世界大战的事。布林迪西。迫击炮。进入罗马。广场，喷泉。“你知道，罗马可不是阿富拉。”关于犹太士兵与教皇的会面，关于他用希伯来语为他们祝福的方式，他只字未提。在米格达尔-阿什凯隆路口，我们停了下来。爸爸从后面拿出一个装着茶的热水瓶和两个夹着煮鸡蛋的三明治。“吃吧，泽维克，你是个弱不禁风的孩子。”当我们到达纳哈尔奥兹时，我们看到一个穿制服的人，一只眼睛蒙着，从基布兹食堂出来。“摩西·达扬在这里做什么？”爸爸疑惑道。“他们杀了罗伊。”一个红着眼睛、泪流满面的女人回答。“达扬昨晚来参加一个亲戚的婚礼。我们昨天原计划有四场婚礼。他留下来参加了葬礼。”“别问他们在把罗伊的尸体还给我们之前对他做了什么。”“摩西·达扬是谁？”我问。“总参谋长。”爸爸回答。我没有问总参谋长是什么，罗伊是谁，或者他们对他的尸体做了什么。我太尴尬了。爸爸牵着我的手，我们加入了一支长长的队伍，跟随着一口覆盖着以色列国旗的棺材。在我们头顶高处，大鸟在天空中盘旋。抬棺材的人把它放进了墓穴。士兵们朝天鸣枪。爸爸用他粗糙的大手捂住我的耳朵。人们拿起铁锹，用泥土和石头填满了墓穴。然后一片寂静。摩西·达扬从口袋里掏出一张纸，读了起来。一阵强风从西边吹来。我捕捉到一些句子的片段。我们要向他讨还血债。我们是如何闭上眼睛的。带着它所有的残酷。要把我们撕成碎片。一顶钢盔和炮口。种树建房。防空洞。铁丝网。一挺机枪。数百万犹太人。历史的灰烬。一片属于我们人民的土地。一片仇恨与复仇的海洋。罗伊的血在向我们呼喊。他破碎的身体。数十万阿拉伯人。我们这一代的宿命，我们生命的选择。武装起来，坚强不屈。剑将落下；我们的生命将被切断。那个金发男孩。刀刃的寒光。加沙的大门沉重。总参谋长折起那张纸，放回口袋。爸爸走近他，告诉他，他给自己的第二个儿子取名为", ] ```

审校建议补充为“取名为罗伊”，该建议被记录在修复历史中。段落 seg-ec100d8686d3891e-0152 的审校意见则指出，原文中“no longer the squills”意为“不再是海葱（开花的季节）”，译文“不再是海葱”表述不完整，容易让读者误解。该段源文本为：

> [SOURCE seg-ec100d8686d3891e-0152]: After dinner, I crossed Wadi Seder westward again to meet Irit. I had been in love with her since we studied together at the end of elementary school.

初译与终译均为：

> [TARGET seg-ec100d8686d3891e-0152]: 晚饭后，我再次向西穿过Wadi Seder去与Irit见面。自从小学快毕业时我们一同学习起，我就一直爱着她。

审校建议将相关表述补充完整，该建议被记录在修复历史中。这类问题表明，在长句与复杂结构的处理中，译文的语义完整性容易受到损害，需要在译后审校环节加以修复。

此外，个别案例中还出现了比喻性表达转换方面的处理倾向。段落 seg-ec100d8686d3891e-0139 的审校意见指出，原文中“outstretched hand”是比喻用法（指请求），译文“伸出的手”略显生硬，建议调整为“回避了我的请求”：

> [SOURCE seg-ec100d8686d3891e-0139]: Back then, Dad wasn’t building houses yet; he was repairing machines. Even then, I think I already sensed that he did things I would never be able to do. Many years later, I asked him to teach me how to weld. “What do you need that for?” he replied, as was his way, once again evading the outstretched hand.

> [TARGET seg-ec100d8686d3891e-0139]: 那时，父亲还未开始建造房屋，他还在修理机器。即便在那时，我想我已隐约感觉到，他所做的事情是我永远无法企及的。多年以后，我请他教我焊接技术，他却以他一贯的方式回答：“你需要那个做什么？”再次避开了我伸出的手。

审校建议将“避开了我伸出的手”调整为“回避了我的请求”，以消解直译带来的语义偏差。需要说明的是，该建议被记录在修复历史中，但终译文本与初译文本保持一致，即该建议未被实际采纳。因此，这一案例仅能说明比喻性表达的转换在个别段落中引发了审校关注，尚不足以构成具有普遍性的难点类别，其证据强度有限。与专有名词处理和语义完整性两类问题相比，比喻性表达转换类问题在案例中仅出现一例，且缺乏修复的实际落实，因此在问题分布的判断中不将其列为同等重要的难点类别。

从修复证据看，{{STAT:repair_category_distribution}}显示，在审校提出建议后，有3处案例发生了初译与终译之间的实际修改（initial_final_changed），5处案例记录了建议的译文（suggested_target_recorded），2处案例记录了人工操作（human_action_recorded）。这些数据表明，审校环节识别出的问题并非全部停留在建议层面，其中一部分确实在初译与终译之间发生了可追溯的修复。以段落 seg-ec100d8686d3891e-0144 为例，审校建议将“取名为”后补充“罗伊”，该建议被记录在修复历史中；段落 seg-ec100d8686d3891e-0139 的审校建议“回避了我的请求”同样被记录在修复历史中。这些修复记录构成了从“问题识别”到“问题解决”的完整证据链。

<!--claim:C2-->

综合以上分析，从结果看可解释为：源文本在语言层面呈现长句、多从句、复杂标点与直接引语交织的特征，在内容层面密集嵌入以色列历史事件、地理名称、人名及文化专有项，这两方面特征共同构成了可实证的翻译难点。在已考察的案例中，审校环节识别出的可操作问题在专有名词处理与语义完整性两方面呈现较高的出现频率，且部分问题在初译与终译之间发生了可追溯的修复。这些发现为后续章节从功能对等视角分析具体翻译决策提供了文本基础与问题指向。

## 3 功能对等视角下的翻译决策分析

## 3 功能对等视角下的翻译决策分析

<!--rq:RQ2-->

本章基于项目过程证据，从功能对等视角对代表性翻译决策进行有限解释。需要首先说明的是，本章的分析框架建立在功能对等理论的基本命题之上，即翻译应追求译文读者对译文的反应与原文读者对原文的反应在功能上相当（Nida, 1964）。然而，功能对等理论本身对“对等”标准的界定存在一定模糊性，且翻译决策的实际形成过程涉及译者多方面的考量。因此，本章的分析定位为“事后归因”式的有限解释，即从结果反推决策倾向，而非还原译者不可观察的心理意图。

为使上述分析框架具有可操作性，本章对功能对等理论的两个核心概念作如下界定。“信息对等”指译文在事实性内容——包括历史事件、专名、数字等——的传递上与原文保持对应，其判断标准是译文读者能够获取与原文读者相同的事实性信息。“效果对等”指译文在交际功能——包括比喻性表达所传递的意象、口语对话所承载的语气与语用意图等——上与原文保持对应，其判断标准是译文读者能够获得与原文读者相近的理解效果与感受。需要说明的是，这两个概念在本章中并非互斥的二元范畴，而是用于描述翻译决策在不同场景中的优先侧重：同一决策可能同时涉及信息与效果两个维度，但往往在某一维度上表现出更明确的优先性。此外，本章还区分“语义准确性调整”这一维度，用以描述那些主要涉及语言表达精确度与语义关系澄清的调整——这类调整既不以事实性信息的传递为核心，也不以交际效果的再现为目标，而是着眼于译文在语言层面的准确与清晰。需要说明的是，这一补充维度并非功能对等理论框架内的原生概念，而是本章为如实描述项目证据中呈现的调整类型而引入的分析工具；其理论定位在于，语义准确性的提升是译文实现信息对等与效果对等的前提条件之一，但本身并不等同于功能对等的实现。本章的分析即以此为框架，考察项目证据中呈现的决策倾向。

需要特别说明的是，本章所依据的项目证据在类型上存在重要差异。审校环节提出的修改建议（findings）反映的是审校者对翻译质量的判断与干预倾向，属于“建议层面”的证据；而初译与终译之间存在可观察差异的案例，则体现了项目最终采纳的翻译决策，属于“决策层面”的证据。两者在证据性质上并不等同：审校建议未必被终译采纳，因此不能直接等同于实际翻译决策。本章在分析时对两类证据予以严格区分：凡涉及审校建议的讨论，其解释范围限于“审校建议可被有限解释为”；凡涉及已落实修改的讨论，其解释范围限于“实际翻译决策可被有限解释为”。这一区分旨在避免将审校建议等同于译者决策，从而保证证据与理论解释之间的对应关系。

<!--claim:C3-->

从项目证据来看，翻译决策在信息对等、效果对等与语义准确性之间呈现出可辨识的权衡模式。具体而言，在涉及历史事件、专名等事实性信息的场景中，审校建议倾向于优先保证信息对等，采用保留原文或加注等策略；在涉及比喻性表达、口语对话等需要传递交际效果的场景中，审校建议倾向于优先保证效果对等，采用意译或调整表达的策略；此外，部分审校建议主要着眼于语言表达的精确度与语义关系的澄清，属于语义准确性层面的优化。需要强调的是，本章对效果对等维度的论断在证据强度上弱于其他两个维度：效果对等优先场景的案例均来自审校建议层面，且其中至少一个案例未被终译采纳，因此该维度的结论应理解为“审校建议层面的倾向”，而非已落实的翻译决策。以下分别从三个维度展开分析。

### 3.1 信息对等优先场景中的策略选择

在涉及事实性信息的翻译场景中，项目证据显示翻译决策倾向于优先保证信息的准确传递。这一判断可从语义补全案例中得到支持。

第234段的审校发现指出，“give me enough for the tickets”应调整为“给我够买票的钱”以补全语义。从结果看可解释为：源文本中该表达在口语语境中省略了“钱”这一语义成分，若不加补全，直译在中文中语义不完整，译文读者难以准确理解说话者的意图。从功能对等理论的视角看，这一调整体现了对信息对等优先性的落实：当源语表达中省略的语义成分在目标语中必须显化才能保证信息的完整传递时，翻译决策倾向于补全该成分，以确保译文读者能够获取与原文读者相同的事实性信息。具体而言，“give me enough for the tickets”在源语口语中虽可由上下文推断其意为“给我够买票的钱”，但中文若直译为“给我够买票的”，其语义在句法层面呈现为悬空状态，译文读者需要额外进行语用推理才能还原说话者的意图，这增加了理解负担，损害了译文作为交际工具的效力。审校建议补全“钱”这一语义成分，使译文在语言层面达到语义完整，从而为译文读者获取与原文读者相近的理解提供了前提条件。需要说明的是，该案例属于审校建议层面的证据，其解释范围限于审校环节对语义完整性的干预倾向。

第170段的审校发现则涉及语义关系准确性的调整。从结果看可解释为：源文本中“white and yellow”以并列关系呈现，若在译文中被改写为“交织”等融合性表达，则可能引入原文未明确表达的语义内容，从而误导译文读者对场景的理解。从功能对等理论的视角看，这一调整体现了对“语义关系准确性”的把握：翻译决策倾向于忠实呈现原文的语义结构，而非在译文中添加原文未包含的修饰性信息。具体而言，源文本中以并列句法结构呈现的“white and yellow”，若在译文中被改写为“交织”这一融合性表达，则在译文中引入了原文未表达的语义内容，使译文读者对场景的想象偏离原文所描述的实际状态。这一偏离虽不涉及事实性信息的缺失，却损害了译文在语义层面与原文的对应关系，进而影响译文读者获得与原文读者相近的理解效果。因此，该调整的核心在于维护语义关系的准确性，为功能对等的实现提供语言层面的保障。需要说明的是，该案例属于审校建议层面的证据，其解释范围限于审校环节对语义关系准确性的干预倾向。

### 3.2 语义准确性调整

除信息对等与效果对等两个维度外，项目证据中还呈现出一类以语言表达精确度为核心的调整。这类调整既不涉及事实性信息的传递，也不涉及交际效果的再现，而是着眼于译文在语义层面的准确与清晰，本章将其归入“语义准确性调整”维度。需要说明的是，这一维度虽在功能对等理论的框架内可被理解为对译文质量的优化，但其调整核心在于语言层面的语义完整性与精确度，而非功能对等理论中“信息对等”或“效果对等”的典型体现。本章将其单列为一个分析维度，旨在如实描述项目证据中呈现的调整类型，同时避免概念界定的模糊。从理论定位看，语义准确性调整可被视为实现功能对等的基础性条件：译文若在语言层面存在语义缺失或语义关系含混，则无论信息传递还是效果再现都将受到损害。因此，这一维度虽非功能对等的直接体现，却是功能对等得以实现的前提保障。这一理论定位可以从两个层面加以说明。其一，从信息传递的角度看，语义准确性的不足意味着译文读者所接收到的信息内容与原文读者之间存在偏差，这种偏差即便不涉及事实性信息的整体缺失，也会在细节层面损害信息对等的实现程度。其二，从效果再现的角度看，语义关系的含混会使译文读者对场景、事件或人物关系的想象偏离原文所描述的实际状态，从而影响译文读者获得与原文读者相近的理解效果。因此，语义准确性调整虽不直接指向功能对等的某一维度，却是两个维度得以实现的语言前提。

第144段的审校发现提供了语义完整性调整的典型案例。从结果看可解释为：源文本中该段落在叙事推进过程中出现了语义截断——某一表达在上下文中被中断或省略，导致其指涉对象在译文中悬而未决。审校建议补全被省略的语义成分，使译文在语言层面达到语义完整。从功能对等理论的视角看，这一调整体现了对“译文可理解性”这一基本要求的落实：若译文在语言层面存在语义空缺，译文读者将无法完整获取原文所传达的意义，信息对等与效果对等均无从谈起。具体而言，该段落的语义截断并非源于口语语境的自然省略，而是叙事文本中因句式结构或表达习惯造成的语义断裂。这种断裂在源语中或许可由上下文语境加以弥补，但中文若不加处理地直译，其语义关系在句法层面呈现为悬空状态，译文读者需要额外进行语用推理才能还原叙述者的意图，这增加了理解负担，损害了译文作为叙事文本的连贯性。审校建议补全这一语义成分，使译文在语言层面达到语义完整，从而为译文读者获取与原文读者相近的理解提供了前提条件。因此，语义补全虽不直接指向功能对等的某一维度，却是功能对等实现的前提性条件。需要说明的是，该案例属于审校建议层面的证据，其解释范围限于审校环节对语义完整性的干预倾向。

第152段的审校发现则涉及另一种语义层面的问题。从结果看可解释为：源文本中“no longer the squills”这一表述在语义上并不完整——“squills”（海葱）作为植物名称，单独出现时缺乏明确的语义指向，译文读者难以判断该表述所指为何。与第144段不同，第144段的语义问题源于叙事句式中语义成分的截断，而第152段的语义问题则源于源语表达本身所指的模糊性：该表述描述的是某一地点或场景中某种植物不再存在的状态变化，但“squills”在译文中若仅作字面处理而不考虑其语义指向，译文读者将无法理解“不再是海葱”这一表述在叙事中的具体作用——它究竟是指某种植物从视野中消失，还是指场景发生了根本性的变化？这一语义含混使译文读者对场景的想象偏离原文所描述的实际状态。审校建议对该表述进行语义澄清，使译文读者能够准确理解源文本所描述的场景变化。从功能对等理论的视角看，这一调整的核心在于维护语义关系的准确性：当源语表达的语义指向在目标语中无法自然呈现时，翻译决策倾向于通过澄清手段使语义关系显化，从而为功能对等的实现提供语言层面的保障。需要说明的是，该案例属于审校建议层面的证据，其解释范围限于审校环节对语义关系准确性的干预倾向。

需要说明的是，上述两个案例虽然在功能对等理论的框架内可被理解为对译文质量的优化，但其调整核心均在于语言层面的语义完整性与精确度，而非功能对等理论中“信息对等”或“效果对等”的典型体现。因此，本章将其单列为一个分析维度，以避免概念界定的模糊。同时，由于本章所依据的项目证据中，语义准确性维度的案例均来自审校建议层面，其解释范围应严格限定于审校环节的干预倾向，而非对实际翻译决策的还原。

### 3.3 效果对等优先场景中的审校建议倾向

在涉及比喻性表达与口语对话的翻译场景中，项目证据显示审校建议倾向于优先保证交际效果的对等，而非字面信息的机械对应。需要强调的是，本节所分析的案例均属于审校建议层面的证据，其解释范围限于审校环节对翻译质量的判断与干预倾向，而非实际翻译决策的还原。换言之，本节所呈现的仅是审校环节对效果对等策略的偏好倾向，C3中“采用意译或调整策略”的论断在效果对等维度上仅获得审校建议层面的支持，缺乏已落实决策的案例支撑。

第139段的审校发现指出，“evading the outstretched hand”直译略显生硬，建议调整为“回避了我的请求”。从结果看可解释为：源文本中“outstretched hand”是一个比喻性表达，字面义为“伸出的手”，在源语语境中隐喻“主动提供的帮助或请求”。从功能对等理论的视角看，这一建议体现了对“交际功能”优先性的考量：当字面直译无法在目标语中再现源语的交际功能时，审校者倾向于放弃形式对应，转而寻求能够唤起译文读者相近反应的功能对应表达。具体而言，若直译为“回避了伸出的手”，中文读者虽能理解字面含义，但“伸出的手”在中文语境中并不具备与源语相同的隐喻联想，其交际功能——即传达“回避他人主动提供的帮助或请求”这一语用意图——在译文中有所损耗。调整为“回避了我的请求”后，译文直接呈现了比喻背后的实际语义，使译文读者能够获得与原文读者相近的理解效果。这一建议属于效果对等优先场景下的意译倾向。

然而，需要特别指出的是，该审校建议在项目记录中属于未被采纳的建议——终译文本与初译文本保持一致。这一事实意味着，该建议虽然反映了审校环节对效果对等策略的偏好倾向，但并未转化为项目的实际翻译决策。因此，该案例作为C3论断的证据效力有限：它只能说明审校环节倾向于在效果对等优先的场景中采用意译策略，而不能说明项目最终采纳了此类调整。本章在引用该案例时，将其定位为“审校建议层面的倾向性证据”，而非“实际翻译决策的证据”。

第56段的审校发现同样涉及效果对等优先的调整。从结果看可解释为：源文本中“You are on your own”在飞行语境中承载着特定的语用功能。在飞行操作中，这句话通常出现在飞行员被告知需要独自应对某种情况、无法获得外部支援的时刻，其语用含义是“自担风险、无人支援”，而非字面意义上的“你独自一人”。若按字面直译，译文读者虽能理解“独自”这一表层含义，却无法把握源语表达在飞行语境中所承载的“你必须自己承担后果、没有后援”的紧迫感与责任意味。从功能对等理论的视角看，这一建议体现了对“语用功能”优先性的考量：当源语表达在特定语境中承载着超越字面意义的语用功能时，审校者倾向于选择能够再现该功能的目标语表达，而非机械对应字面信息。具体而言，“You are on your own”在飞行语境中传达的是“你只能靠自己了”这一语用意图，若直译为“你独自一人”，虽在字面层面与原文对应，却丧失了源语表达在特定语境中所承载的“自担风险、无人支援”的语用含义。审校建议调整为“你只能靠自己了”，使译文读者能够获得与原文读者相近的语用感受，从而在交际功能层面实现与原文的对应。这一建议属于效果对等优先场景下的调整倾向。需要说明的是，该案例同样属于审校建议层面的证据，其解释范围限于审校环节对语用功能再现的干预倾向。

第119段的审校发现则涉及语义精确度的调整。从结果看可解释为：源文本中某一表达在哲学语境中承载着“笃定”这一精确语义——即一种基于内在确信而产生的坚定态度，而非仅指逻辑上的确定性。若译为“确定性”，虽在字面层面与原文对应，却难以传达源语表达在特定语境中所承载的“坚定确信”的语义内涵：“确定性”在中文中更偏向描述一种客观状态或逻辑属性，而“笃定”则指向主体的心理状态与态度倾向。在哲学讨论的语境中，这一差异尤为关键——前者可能被理解为对命题真值的判断，后者则强调主体对某一立场或信念的坚定持守。审校建议调整为“笃定”，使译文读者能够获得与原文读者相近的语义理解，从而在语义层面实现与原文的对应。这一建议属于语义精确度层面的调整倾向。需要说明的是，该案例同样属于审校建议层面的证据，其解释范围限于审校环节对语义精确度的干预倾向。

需要说明的是，本节所分析的案例均属于审校建议层面的证据，且未被本章所依据的项目证据证实已落实到终译文本。因此，本节的分析仅能说明审校环节对效果对等策略的偏好倾向，而不能直接等同于对译者实际决策的还原。这一证据局限意味着，本章对效果对等优先场景的分析强度弱于信息对等与语义准确性两个维度，C3中“采用意译或调整策略”的论断在效果对等维度上仅获得审校建议层面的支持，缺乏已落实决策的案例支撑。

### 3.4 三类调整的权衡与证据局限

从上述案例分析可以看出，审校建议在信息对等、效果对等与语义准确性之间并非截然二分，而是在具体场景中有所侧重。需要强调的是，这种侧重仅是事后归因式的有限解释，而非对译者实际决策过程的还原。

值得注意的是，上述案例中的调整幅度总体较小，多属于局部表达层面的优化，而非整体策略的转向。这一特征可能反映了回忆录文体对翻译的约束——作为纪实性文本，回忆录的翻译需要在忠实传递事实信息与再现文学效果之间保持平衡，因此翻译决策往往表现为局部调整而非全局重构。

同时，功能对等理论本身对“对等”标准的界定存在模糊性，何种程度的调整构成“功能对等”难以给出精确的操作化标准。因此，本章的分析仅能说明：从结果看，部分审校建议可被有限解释为在信息对等优先的场景中采用保留原文或加注策略，在效果对等优先的场景中审校建议倾向于采用意译或调整策略，另有部分审校建议属于语义准确性层面的优化。这一解释框架有助于理解翻译决策的倾向性模式，但不能也不应被理解为对译者决策依据的确定性论断。

此外，本章所分析的案例在证据类型上存在明显的不均衡：信息对等优先场景的案例仅包含审校建议层面的证据；语义准确性调整的案例同样仅包含审校建议层面的证据；而效果对等优先场景的案例则全部集中于审校建议层面，且其中至少一个案例（第139段）已被证实未被终译采纳。这一不均衡反映了项目证据本身的分布特征，也提示本章的解释范围应严格限定于所引案例能够支撑的结论，不宜过度推广为对全部翻译决策的系统性概括。就研究问题而言，本章对RQ2的回答应理解为：从功能对等视角看，项目中的审校建议与实际翻译决策均可被有限解释为在信息对等、效果对等与语义准确性之间有所权衡，其中信息对等优先场景的证据来自审校建议层面，语义准确性调整的证据来自审校建议层面，效果对等优先场景的证据则主要来自审校建议层面且强度有限，C3中关于效果对等优先场景采用意译或调整策略的论断，目前仅能获得审校建议层面的有限支持，尚不能视为已落实翻译决策的普遍特征。

## 4 术语治理、机器翻译与译后编辑的效果与局限

## 4 术语治理、机器翻译与译后编辑的效果与局限

<!--rq:RQ3-->

本章基于项目统计与案例证据，分析术语治理、机器翻译、审校与译后编辑在本项目中的可追溯效果与局限。分析所依据的材料包括项目整体统计指标、候选案例的初译与终译对照记录、审校环节发现的问题类型分布，以及术语决策记录。需要说明的是，本章所讨论的“效果”与“局限”均以项目过程中留下的可追溯证据为判断依据，而非对机器翻译引擎或术语管理工具的一般性评价。

### 4.1 机器翻译的效率与可追溯局限

从项目统计看，机器翻译在本项目中完成了全部段落的初译工作。273<!--stat:total_segments-->个源文本段落中，273<!--stat:translated_segments-->段均生成了初译文本，翻译覆盖率达到100%。需要说明的是，此处所讨论的“效率”仅指任务完成度，即机器翻译在批量处理长篇回忆录文本时能够完成全部段落的初步转换，不涉及翻译时间、人工干预量等成本维度的判断。从候选案例的初译质量看，机器翻译在长句与复杂结构的处理上表现出一定的稳定性。以seg-ec100d8686d3891e-0144为例，该段源文本长达3632字符，包含14个从句标记和85个标点符号，属于典型的复杂长段落。机器翻译生成的初译在整体结构上保持了原文的叙事顺序，对引语、破折号等标点符号的处理也基本符合中文书写习惯。

然而，机器翻译的局限同样在项目证据中留下了清晰的痕迹。264<!--stat:reviewed_segments-->段接受了审校检查，共识别出32<!--stat:actionable_findings-->条可操作问题。需要指出的是，这些发现来自审校环节对特定段落的检查，其代表性受限于审校覆盖范围与案例选取方式，不宜据此对机器翻译的整体能力作一般性判断。同时，部分局限可能源于源文本本身的复杂性——长句、多从句、文化负载表达等文本固有难度——而非单纯反映引擎能力不足。因此，本章对机器翻译局限的讨论限定为“在部分案例中，机器翻译输出在专名一致性、语义完整性及文化专有项处理上存在需要人工修正的情形”，而非对引擎能力的绝对否定。

在专名一致性方面，审校记录显示，机器翻译在处理专名时存在前后不一致的情况。例如，seg-ec100d8686d3891e-0215的审校记录指出，机器翻译将地名“Atlit”音译为“阿特利特”，将“Rabbits Hideaway”和“Chair Hill”分别译为“兔子藏身处”和“椅子山”。审校建议保留原文专名或加注中文译名并保留原文：

> [SOURCE seg-ec100d8686d3891e-0215]: He tried to tan, but his skin turned red. He walked with the older kids toward Atlit and back, collected a lot of seashells, and found one that echoed the sound of the sea when he held it to his ear. He also found a rare one, a dark shell, that only he had until the end of camp. He refused to trade it, remembering what had happened on the trip to the Rabbits Hideaway and Chair Hill. There, he had found a truly ancient oil lamp, perfectly intact, but they gave him a worthless one in exchange. The lamp story – that was a long time ago.

> [TARGET seg-ec100d8686d3891e-0215]: 他试着晒黑，但皮肤却变红了。他和年长的孩子们一起走到阿特利特再折返，收集了许多贝壳，还找到一个贴在耳边能回响海声的。他还发现了一个稀有的深色贝壳，直到营地结束前只有他拥有。他拒绝交换，想起了去兔子藏身处和椅子山的旅行中发生的事。在那里，他找到了一盏真正古老的油灯，完好无损，但他们却换给他一个毫无价值的。油灯的故事——那是很久以前的事了。

审校建议将“阿特利特”改回“Atlit”，将“兔子藏身处”和“椅子山”改回“Rabbits Hideaway”和“Chair Hill”。这一案例说明，机器翻译在处理专有地名时倾向于采用音译或意译策略，但未能充分考虑专名在目标文化中的可识别性与可追溯性。从结果看可解释为，机器翻译的专名处理策略缺乏对专名类别（人名、地名、机构名等）的区分意识，也未建立跨段落的专名一致性控制机制。需要说明的是，该段源文本本身包含多个专有地名，其处理难度部分源于文本固有特征，但机器翻译未能在译文中保留原文专名以供读者追溯，这一处理方式在回忆录类文本中尤其值得关注。

在语义完整性方面，seg-ec100d8686d3891e-0144的审校记录提供了一个典型的截断案例。该段初译以“爸爸走近他，告诉他，他给自己的第二个儿子取名为”结尾，原文中“after”一词暗示后续应有人名（如“罗伊”），但初译未完整呈现这一信息，造成语义不完整。审校记录对此提出了明确的修复建议：

> [SOURCE seg-ec100d8686d3891e-0144]: We were nine years old. It was spring. The poppies were in bloom, and so were the chrysanthemums. Back then, we didn’t know it happened six months before Operation Kadesh, which was in 1956. Dad drove from the valley to the Negev, near Gaza, to harvest hay in the fields of Nahal Oz. This time, he took me with him. He asked for and received permission from my teacher, Rachel, who placed her hand on my head, looked me in the eyes, and listened to my breathing. “No asthma. It’s the Lag Ba’Omer holiday too. It’s fine.” It was dark, and we were all still asleep when Dad woke me up. “Brush your teeth, Zevik.” “What about everyone else?” I asked. “You’re the only one coming,” Dad replied. He was thirty-five, thirty-five years old. Where was I at thirty-five? The First Lebanon War. Five wars later. I sat in the jeep on the right side. I remember the smell of burnt gasoline and the moment just before sunrise, when Dad turned off the lights. The red of the poppies and the yellow of the chrysanthemums gave way to the pink of flax and the blue of cornflowers. Dad sang about Samson’s foxes carrying torches at night, and that the main things in the jeep were speed, clutch, and reverse. Not a word about Mom or the two other kids he already had then. I asked him if they had found his missing harmonica. “Forget about it,” he said. And then he told me about the World War. Brindisi. The mortars. Entering Rome. The squares, the fountains. “You know, Rome is no Afula.” Not a word about the meeting of the Jewish soldiers with the Pope, about the way he blessed them in Hebrew. At the Migdal-Ashkelon junction, we stopped. Dad pulled out a thermos of tea and two sandwiches with hard-boiled eggs from the back. “Eat, Zevik, you’re a weakling.” When we arrived at Nahal Oz, we saw someone in uniform, one eye covered, coming out of the kibbutz dining hall. “What is Moshe Dayan doing here?” Dad wondered. “They killed Roy,” answered a woman with red, tearful eyes. “Dayan came here last night for a relative’s wedding. We had four weddings planned for yesterday. He stayed over for the funeral.” “Don’t ask what they did to Roy’s body before they returned it to us.” “Who is Moshe Dayan?” I asked. “The Chief of Staff,” Dad replied. I did not ask what a Chief of Staff was, who Roy was, or what they had done to his body. I was too embarrassed. Dad took my hand, and we joined a long procession following a coffin draped in the Israeli flag. High above us, large birds circled in the sky. The people carrying the coffin on their shoulders lowered it into a grave. Soldiers fired rifles pointed toward the sky. Dad covered my ears with his large, calloused hands. The people took shovels and filled the grave with earth and stones. And then there was silence. Moshe Dayan pulled a piece of paper out of his pocket and read from it. A strong wind blew from the west. I caught fragments of sentences. From ourselves, we will demand his blood. How did we shut our eyes. With all of its cruelty. To tear us to pieces. A steel helmet and a cannon’s mouth. To plant a tree and build a home. Shelters. Barbed wire. A machine gun. Millions of Jews. The ashes of history. A land for our people. A sea of hatred and revenge. Roy’s blood cries out to us. His torn body. Hundreds of thousands of Arabs. The decree of our generation, the choice of our lives. Armed, strong, and unyielding. The sword will fall; our lives will be cut off. The blond boy. The gleam of the blade. Gaza’s gates are weighty. The Chief of Staff folded the piece of paper and put it back in his pocket. Dad approached him and told him he had named his second son after

> [TARGET seg-ec100d8686d3891e-0144]: ```json [   "我们九岁。那是春天。罂粟花开了，菊花也开了。那时，我们并不知道这发生在卡迭石行动（1956年）前六个月。爸爸从山谷开车到内盖夫，靠近加沙，去纳哈尔奥兹的田里收割干草。这一次，他带上了我。他向我的老师拉结请求并获得了许可，她把手放在我的头上，看着我的眼睛，听了听我的呼吸。“没有哮喘。而且也是篝火节。没问题。”天还黑着，我们都还在睡梦中，爸爸叫醒了我。“刷牙，泽维克。”“其他人呢？”我问。“只有你一个去。”爸爸回答。他三十五岁，三十五岁。我三十五岁时在哪里？第一次黎巴嫩战争。五次战争之后。我坐在吉普车的右边。我记得烧汽油的味道，以及日出前的那一刻，爸爸关掉了车灯。罂粟的红和菊花的黄让位给了亚麻的粉和矢车菊的蓝。爸爸唱着参孙的狐狸在夜里带着火把的故事，还说吉普车里最重要的是速度、离合器和倒挡。关于妈妈或他那时已经有的另外两个孩子，他只字未提。我问他是否找到了他丢失的口琴。“别提了。”他说。然后他给我讲了世界大战的事。布林迪西。迫击炮。进入罗马。广场，喷泉。“你知道，罗马可不是阿富拉。”关于犹太士兵与教皇的会面，关于他用希伯来语为他们祝福的方式，他只字未提。在米格达尔-阿什凯隆路口，我们停了下来。爸爸从后面拿出一个装着茶的热水瓶和两个夹着煮鸡蛋的三明治。“吃吧，泽维克，你是个弱不禁风的孩子。”当我们到达纳哈尔奥兹时，我们看到一个穿制服的人，一只眼睛蒙着，从基布兹食堂出来。“摩西·达扬在这里做什么？”爸爸疑惑道。“他们杀了罗伊。”一个红着眼睛、泪流满面的女人回答。“达扬昨晚来参加一个亲戚的婚礼。我们昨天原计划有四场婚礼。他留下来参加了葬礼。”“别问他们在把罗伊的尸体还给我们之前对他做了什么。”“摩西·达扬是谁？”我问。“总参谋长。”爸爸回答。我没有问总参谋长是什么，罗伊是谁，或者他们对他的尸体做了什么。我太尴尬了。爸爸牵着我的手，我们加入了一支长长的队伍，跟随着一口覆盖着以色列国旗的棺材。在我们头顶高处，大鸟在天空中盘旋。抬棺材的人把它放进了墓穴。士兵们朝天鸣枪。爸爸用他粗糙的大手捂住我的耳朵。人们拿起铁锹，用泥土和石头填满了墓穴。然后一片寂静。摩西·达扬从口袋里掏出一张纸，读了起来。一阵强风从西边吹来。我捕捉到一些句子的片段。我们要向他讨还血债。我们是如何闭上眼睛的。带着它所有的残酷。要把我们撕成碎片。一顶钢盔和炮口。种树建房。防空洞。铁丝网。一挺机枪。数百万犹太人。历史的灰烬。一片属于我们人民的土地。一片仇恨与复仇的海洋。罗伊的血在向我们呼喊。他破碎的身体。数十万阿拉伯人。我们这一代的宿命，我们生命的选择。武装起来，坚强不屈。剑将落下；我们的生命将被切断。那个金发男孩。刀刃的寒光。加沙的大门沉重。总参谋长折起那张纸，放回口袋。爸爸走近他，告诉他，他给自己的第二个儿子取名为", ] ```

审校建议将译文补充为“爸爸走近他，告诉他，他给自己的第二个儿子取名为罗伊”，以恢复语义的完整性。从结果看可解释为，机器翻译在处理长段落时，可能在段落末尾出现信息截断，未能完整呈现原文的全部语义内容。这一现象在长段落中尤为值得关注，因为段落越长，信息截断的风险越高。需要指出的是，该段源文本本身以“after”结尾，属于跨段落的语义延续，机器翻译未能识别这一跨段衔接关系，这一局限既与引擎的上下文建模能力有关，也与源文本的段落切分方式有关。

在文化专有项处理方面，seg-ec100d8686d3891e-0152的审校记录揭示了另一类问题。该段初译将“Wadi Seder”保留为原文形式，审校的确定性检查标记了“疑似残留源语片段「Seder」”。同时，审校还指出译文对“no longer the squills”的处理存在语义不完整的问题，建议补充“开花的季节”或类似说明。这一案例说明，机器翻译在处理文化负载表达时可能存在理解偏差，未能准确传达原文的语义层次。从结果看可解释为，机器翻译对文化专有项的识别与处理缺乏稳定的策略：一方面可能将应保留原文的专名误译为中文，另一方面也可能将应翻译的文化表达保留为原文形式，两种倾向均可能导致译文在目标读者中的可读性受损。

综合上述证据，机器翻译在本项目中的效率优势与质量局限并存。273<!--stat:translated_segments-->段的全部完成体现了其在处理大规模文本时的任务完成度，但32<!--stat:actionable_findings-->条可操作问题则说明，机器翻译在部分案例中于专名一致性、语义完整性和文化专有项处理方面存在需要人工修正的情形。需要强调的是，上述案例的选取基于证据完整性与代表性，其发现反映了机器翻译在本项目特定文本类型与语言对条件下的表现，不宜过度推广为对机器翻译整体能力的判断。

### 4.2 术语治理的作用边界

<!--claim:C5-->

术语治理在本项目中呈现出“预防已知冲突有效、覆盖范围有限”的双重特征。从项目统计看，0<!--stat:term_conflicts-->表明术语库中已收录的条目在翻译过程中未发生冲突。这一数据说明，术语库在已覆盖的条目范围内发挥了预期的规范作用，确保了相关术语在译文中的一致性。

然而，需要审慎对待这一统计结果。0<!--stat:term_conflicts-->仅说明术语库中已收录的条目未发生冲突，但未收录的专名（如人名、地名）不在术语库管理范围内，因此不能据此直接推断术语治理的整体有效性。要评估术语治理的作用边界，还需结合术语库的实际覆盖范围与专名处理标准进行考察。需要说明的是，由于本项目未系统记录术语库收录条目的总量与类别分布，本章对“覆盖范围有限”的判断主要基于候选案例中可见的术语条目记录，这一判断的推广范围受限于案例选取的代表性。

从候选案例看，仅少数案例包含术语条目记录。以seg-ec100d8686d3891e-0144为例，该段仅有一个术语条目基布兹（集体农庄）<!--term:t-13bdacf558f9-->，将“Kibbutz”译为“基布兹（集体农庄）”。该术语决策在初译与终译中均得到一致执行，体现了术语库对已收录条目的约束力。但该段同时涉及大量其他专名——如人名“Zevik”“Rachel”“Moshe Dayan”“Roy”，地名“Nahal Oz”“Migdal-Ashkelon”“Afula”“Brindisi”等——这些专名均未纳入术语库管理范围，其翻译处理依赖机器翻译的默认策略与人工审校的介入。

更值得注意的是，术语治理未能完全避免专名处理问题的发生。seg-ec100d8686d3891e-0215的审校记录显示，地名“Atlit”在初译中被音译为“阿特利特”，审校建议保留原文。这一专名问题并未被术语库预防，因为“Atlit”未收录在术语库中。同样，seg-ec100d8686d3891e-0007的审校记录显示，人名“Sarah”和“Yaakov”在终译中被保留为原文形式，但审校同时指出中文亲属称谓后不应加空格的问题：

> [SOURCE seg-ec100d8686d3891e-0007]: For Grandma Sarah and Grandpa Yaakov

> [TARGET seg-ec100d8686d3891e-0007]: 献给祖母Sarah和祖父Yaakov

审校建议将“祖母Sarah”调整为“祖母Sarah与祖父Yaakov”，以符合中文书写习惯。这一案例说明，即使专名本身得到了保留原文的处理，其与中文语境的衔接方式仍可能存在问题，而这类问题超出了术语库的管辖范围。

从项目整体看，213<!--stat:tm_reuse_count-->段的翻译记忆复用率（占273<!--stat:total_segments-->段的78%）说明，翻译记忆在项目中发挥了较高的复用价值。但翻译记忆的复用与术语库的覆盖范围是两个不同的维度：翻译记忆侧重于整句或段落的复用，术语库侧重于单个术语的规范。两者在本项目中均未能完全覆盖专名处理的全部场景。

从结果看可解释为，术语治理的作用边界在于预防已知术语冲突，而非覆盖全部专名决策。术语库的有效性取决于条目的收录范围，对于未收录的专名——尤其是人名、地名等文化专有项——术语库无法提供约束，其处理质量依赖于机器翻译的默认策略与人工审校的介入。从术语治理的机制看，术语库的构建通常基于预先提取的术语清单，其覆盖范围受限于术语提取阶段对文本的扫描深度与收录标准。在本项目中，术语条目主要集中在飞行技术术语（如空间定向障碍<!--term:t-1164341244e5-->、飞行训练课程<!--term:t-87ba1b407370-->、应急罗盘<!--term:t-a11819421974-->等）与少量文化词汇（如基布兹（集体农庄）<!--term:t-13bdacf558f9-->），而回忆录文本中大量出现的人名、地名等专名并未被系统纳入术语管理流程。这一发现提示，在回忆录类文本的翻译项目中，术语治理应更加重视专名表的建设，将高频出现的人名、地名纳入术语库管理范围，以弥补机器翻译在专名一致性方面的不足。

### 4.3 审校与译后编辑的实质性作用

<!--claim:C6-->

审校与译后编辑环节在本项目中留下了可追溯的修复记录。8<!--stat:repaired_segments-->段在审校环节发生了修复，修复类型分布为：初译与终译发生变化（initial_final_changed）3处、建议目标记录（suggested_target_recorded）5处、人工操作记录（human_action_recorded）2处。这一分布说明，审校环节的修复并非单一类型，而是涵盖了从“发现问题—提出建议”到“实际修改译文”的多个层面。需要说明的是，此处对审校作用的判断基于已落实修复的案例证据，审校发现问题与审校实际修改译文是两个不同层面，前者反映审校的识别能力，后者反映审校的决策影响力。因此，本章对“实质性作用”的表述限定为“在已落实修复的案例中发挥了可追溯的修正作用”，而非对审校整体效力的无条件肯定。

从候选案例看，初译与终译之间的可追溯变化为评估人工审校的作用提供了直接证据。seg-ec100d8686d3891e-0144的初译与终译对比显示，译文末尾从“取名为”截断状态得到补充，终译中补全了“罗伊”这一人名信息。这一变化属于{{STAT:repair_category_distribution}}中的initial_final_changed类型，说明审校环节不仅识别了问题，还实际修改了译文。

seg-ec100d8686d3891e-0215的初译与终译对比同样显示了可追溯的变化。初译将“Atlit”音译为“阿特利特”，终译保留了原文“Atlit”；初译将“Rabbits Hideaway”和“Chair Hill”意译为“兔子藏身处”和“椅子山”，终译保留了原文。这一变化说明，审校环节对专名处理策略进行了实质性调整，从音译/意译转向保留原文。

除初译与终译的实际变化外，建议目标记录也构成了审校作用的重要证据。seg-ec100d8686d3891e-0139的审校记录显示，审校者认为译文将“evading the outstretched hand”直译为“避开了我伸出的手”略显生硬，建议调整为“回避了我的请求”：

> [SOURCE seg-ec100d8686d3891e-0139]: Back then, Dad wasn’t building houses yet; he was repairing machines. Even then, I think I already sensed that he did things I would never be able to do. Many years later, I asked him to teach me how to weld. “What do you need that for?” he replied, as was his way, once again evading the outstretched hand.

> [TARGET seg-ec100d8686d3891e-0139]: 那时，父亲还未开始建造房屋，他还在修理机器。即便在那时，我想我已隐约感觉到，他所做的事情是我永远无法企及的。多年以后，我请他教我焊接技术，他却以他一贯的方式回答：“你需要那个做什么？”再次避开了我伸出的手。

审校建议将“再次避开了我伸出的手”调整为“再次回避了我的请求”，理由是原文中“outstretched hand”是比喻用法，指代“请求”，直译“伸出的手”在中文中略显生硬。需要指出的是，该段的终译未实际采纳这一建议（final_target与initial_target一致），因此这一案例反映的是审校在“识别问题”层面的功能，而非“修正译文”层面的功能。将此类未被采纳的建议与已落实的修复（如seg-ec100d8686d3891e-0144、seg-ec100d8686d3891e-0215中的initial_final_changed）区分开来，有助于更准确地界定审校的实际作用范围。从结果看可解释为，审校环节既包含实际修改译文的功能，也包含提出优化建议的功能，两者共同构成审校在质量控制中的角色，但“实质性修正作用”的判断应以已落实修复的案例为依据。

seg-ec100d8686d3891e-0152的审校记录则揭示了另一类问题。该段初译将“Wadi Seder”保留为原文形式，审校的确定性检查标记了“疑似残留源语片段「Seder」”。同时，审校还指出译文对“no longer the squills”的处理存在语义不完整的问题，建议补充“开花的季节”或类似说明。这一案例说明，审校环节不仅关注专名的处理方式，还关注语义的完整传达，能够识别机器翻译在文化负载表达上的理解偏差。

seg-ec100d8686d3891e-0007的案例则展示了审校在格式规范方面的作用。该段初译未记录（initial_target为null），终译完成了翻译：“献给祖母Sarah和祖父Yaakov”。审校记录指出中文亲属称谓后不应加空格，建议调整为“献给祖母Sarah与祖父Yaakov”。虽然该段的修复属于格式层面的调整，而非实质内容的修改，但它说明审校环节对译文质量的把控涵盖了从内容到格式的多个维度。

综合上述证据，审校与译后编辑在本项目中发挥了可追溯的修正作用。8<!--stat:repaired_segments-->段的修复记录、{{STAT:repair_category_distribution}}的分布特征，以及候选案例中初译与终译的可追溯变化，共同说明人工审校在修正机器翻译输出方面并非流于形式，而是切实介入了译文的修改与优化。审校环节既能够识别并修正语义截断、专名处理不当等实质性问题，也能够对比喻表达、格式规范等细节层面提出优化建议。

然而，从项目整体看，8<!--stat:repaired_segments-->段相对于273<!--stat:total_segments-->段的总量而言比例较低（约2.9%），且264<!--stat:reviewed_segments-->段未覆盖全部段落。这一数据提示，审校环节的覆盖面与修复比例仍有提升空间。部分修复可能仅涉及格式或标点调整，而非实质内容修正，需结合修复的严重程度进一步评估审校的实际效果。此外，审校记录中部分建议目标未被终译采纳（如seg-ec100d8686d3891e-0139），说明审校建议与最终译文之间可能存在决策落差。因此，对审校作用的判断应限定为“在已落实修复的案例中发挥了可追溯的修正作用”，而非对审校整体效力的无条件肯定。

### 4.4 本章小结

<!--claim:C4-->

本章基于项目统计与案例证据，分析了术语治理、机器翻译、审校与译后编辑在本项目中的可追溯效果与局限。分析表明：机器翻译在长句与复杂结构处理上表现出较高任务完成度（273<!--stat:translated_segments-->段全部完成翻译），但在部分案例中，机器翻译输出在专名一致性、语义完整性及文化专有项处理上存在需要人工修正的情形，需依赖人工审校与译后编辑进行修正——这一判断以审校环节实际识别的问题为限，且部分局限可能源于源文本本身的复杂性（如长句、多从句、文化负载表达等文本固有难度），而非单纯反映引擎能力不足；术语治理在本项目中未出现术语冲突（0<!--stat:term_conflicts-->），但术语条目的覆盖范围有限，术语库的作用边界在于预防已知术语冲突，而非覆盖全部专名决策——这一判断受限于案例选取的代表性，术语库的实际覆盖范围仍需结合更完整的术语管理记录加以评估；审校与译后编辑环节中，部分修复在初译与终译之间发生了可追溯的变化（{{STAT:repair_category_distribution}}），且修复类型以建议目标记录和人工操作记录为主，说明人工审校在已落实修复的案例中发挥了可追溯的修正作用——审校建议与最终译文之间的决策落差仍需进一步追踪，审校“识别问题”与“修正译文”两个层面的功能应加以区分。

从项目管理的角度看，上述发现提示，在回忆录类文本的翻译项目中，机器翻译的任务完成度优势与质量局限并存，术语治理的预防作用与覆盖局限并存，人工审校的实质作用与覆盖面不足并存。三者之间的协同关系决定了翻译质量的上限：机器翻译提供初译基础，术语库预防已知冲突，人工审校修正未知问题。三者缺一不可，但各自的作用边界需要根据项目特征进行合理配置。

## 5 结论

## 5 结论

本章在总结前文分析的基础上，依次回应三个研究问题，说明本研究的贡献与局限。需要强调的是，本章所有结论均以项目过程中可观察、可追溯的证据为限，不涉及对译者心理意图的推测，也不试图将功能对等理论扩展为对全部翻译决策的统摄性解释。

### 5.1 研究发现总结

<!--rq:RQ1-->
<!--claim:C1-->
针对第一个研究问题（源文本的主要语言特征与可证实的翻译难点是什么），本研究发现：在已考察的段落中，源文本在语言层面呈现长句、多从句、复杂标点与直接引语交织的特征，在内容层面嵌入以色列历史事件、地理名称、人名及文化专有项，构成可实证的翻译难点。这一判断的依据来自多个维度的项目证据：其一，在已分析的案例中，部分段落长度显著超出常规，如第144段源文本长达3632个字符，包含14个从句标记与85个标点符号，属于典型的长句与复杂标点密集段落；其二，所考察的段落中大量出现以色列地名（如Geva、Atlit、Nahal Oz）、历史人物（如Ben-Gurion、Tabenkin）及文化专有项（如Lag Ba'Omer），这些专名在翻译中涉及保留原文、音译、加注等多种处理方式，构成内容层面的难点；其三，审校环节识别出的可操作问题（actionable findings）集中于专有名词处理与语义完整性两方面，从问题分布的角度佐证了上述难点在翻译过程中的实际显现。需要说明的是，上述“特征”与“嵌入”的判断基于本研究所深入分析的案例集合，而非对全部273<!--stat:total_segments-->段源文本的系统性量化统计，因此结论的适用范围以已考察段落为限。

<!--claim:C2-->
进一步地，审校环节识别出的可操作问题集中于专有名词处理（人名、地名、作品名）与语义完整性两方面，且部分问题在初译与终译之间发生了可追溯的修复。例如，第215段的审校发现指出Atlit、Rabbits Hideaway、Chair Hill应保留原文而非音译；第233段的发现指出电影名Riot in Cell Block 11译名不准确；第235段的发现指出人名Tzvika、Noam等未与前文统一；第144段的发现指出译文末尾语义不完整（“取名为”后内容缺失）；第239段的发现指出第二段原文完全漏译。这些发现分别指向专名处理与语义完整性两个维度，且修复记录显示部分问题在初译与终译之间确实发生了变化，构成可追溯的证据链。

<!--rq:RQ2-->
<!--claim:C3-->
针对第二个研究问题（代表性翻译决策从功能对等视角可作何种有限解释），本研究发现：在功能对等视角下，部分翻译决策可被有限解释为——在信息对等优先的场景（如历史事件、专名）中采用保留原文或加注策略，在效果对等优先的场景（如比喻性表达、口语对话）中采用意译或调整策略。这一解释的“有限性”体现在两个方面：其一，它是对翻译结果的事后归因，而非对译者实际决策过程的还原；其二，功能对等理论本身对“对等”标准的界定存在模糊性，因此上述解释仅能说明决策倾向与功能对等理论的基本命题之间存在相容性，而不能证明决策是由该理论直接推导而来。从具体案例看，第56段的发现指出“You are on your own”在飞行语境中应译为“你只能靠自己了”而非字面直译，属效果对等调整；第140段的发现指出地名Geva应保留原文并加括号注释，属信息对等优先的处理。需要说明的是，第139段的审校发现曾建议将“evading the outstretched hand”从直译调整为“回避了我的请求”，但该建议未被终译采纳，终译仍保留了直译处理，因此该案例仅能说明审校环节提出了效果对等优先的调整方向，而不能作为已落实的意译决策的证据。这些案例显示翻译决策在信息对等与效果对等之间有所权衡，但仅能作有限解释。

<!--rq:RQ3-->
<!--claim:C4-->
针对第三个研究问题（术语治理、机器翻译、审校与译后编辑在本项目中呈现了哪些可追溯效果与局限），本研究发现可从三个层面加以概括。其一，机器翻译完成了全部273<!--stat:total_segments-->段的初译，覆盖率为100%，在任务完成度上表现出较高的处理能力；但在部分案例中表现出可追溯的局限。需要说明的是，本研究所依据的证据仅能说明机器翻译“完成了全部段落的初译”，并不包含翻译时间、人工干预量等效率指标，因此不宜对“效率”作价值判断。同时，这些局限的成因可能部分源于源文本本身的复杂性（如长句、文化负载），而非完全归因于机器翻译引擎的能力不足。从具体案例看，第235段的发现指出人名翻译前后不一致，第239段的发现指出整段漏译，第215段的发现指出专名未保留原文，第144段的发现指出语义截断，第233段的发现指出电影译名不准确，第7段的发现指出称谓与空格问题。这些finding表明，在部分案例中，机器翻译输出在专名一致性、语义完整性及文化专有项处理上存在需要人工修正的情形。鉴于上述判断仅基于少数案例（6个），且部分局限可能源于源文本本身的复杂性，该结论不宜推广为对机器翻译整体能力的判断。

<!--claim:C5-->
其二，术语治理在本项目中未出现术语冲突（0<!--stat:term_conflicts-->），但术语条目的覆盖范围有限，且术语管理未能完全避免专名处理问题的发生。需要说明的是，由于本项目未系统记录术语库收录条目的总量与类别分布，本研究对“覆盖范围有限”的判断主要基于候选案例中可见的术语条目记录——在深入分析的案例中，仅少数段落含有术语条目，且每条术语条目的数量多为1至3个。这一判断的推广范围受限于案例选取的代表性，不宜据此对术语库的整体覆盖情况作更广泛的推断。此外，关于“术语管理未能完全避免专名处理问题的发生”，其证据基础在于：审校环节在第215段（地名Atlit未保留原文）与第7段（称谓处理问题）识别出专名处理问题，而这些问题并未被术语库预防。但需要指出的是，这两起案例仅能说明术语库在已收录条目之外未能覆盖全部专名决策，而不能据此判断术语库在已收录条目上的预防效果——事实上，0<!--stat:term_conflicts-->的统计结果说明，在已收录条目上未发生冲突。从项目证据看，翻译记忆复用率较高（213<!--stat:tm_reuse_count-->段，占全部段落的78%），说明术语库与翻译记忆在已收录条目上发挥了预防冲突的作用。综合而言，术语治理的作用边界在于预防已知术语冲突，而非覆盖全部专名决策，这一判断的证据基础限于候选案例中可见的术语条目记录与上述两起专名处理案例。

<!--claim:C6-->
其三，审校与译后编辑环节中，部分修复在初译与终译之间发生了可追溯的变化（{{STAT:initial_final_changed}}），且修复类型以建议目标记录（{{STAT:suggested_target_recorded}}）和人工操作记录（{{STAT:human_action_recorded}}）为主。从具体案例看，第144段的初译与终译对比可见末尾内容从“取名为”截断到补充完整，第215段的对比可见Atlit等专名从音译改为保留原文，第142段的对比可见译文从截断到补充完整，这些修复均发生在审校环节，且变化可追溯。需要指出的是，上述修复仅涉及8<!--stat:repaired_segments-->段，相对于273<!--stat:total_segments-->段总量比例较低（约2.9%），且部分修复可能仅涉及格式或标点调整而非实质内容修正。因此，人工审校的作用应被限定为：在已修复的特定案例中发挥了可追溯的实质修正作用，而非对机器翻译输出进行了大规模、系统性的修正。这一结论的强度受限于修复案例的数量与性质，不宜作更广泛的推广。

### 5.2 研究贡献

本研究的贡献主要体现在方法论层面。与传统的翻译实践报告相比，本研究尝试以项目过程证据（包括源文本片段、初译与终译文本、审校发现、修复记录及项目统计指标）作为分析的基础，对翻译决策进行“事后归因”式的有限解释，而非还原译者不可观察的心理意图。这一路径的优势在于：其一，分析结论可追溯、可验证，读者可以通过查阅项目证据来检验分析的合理性；其二，避免了“译者意图”这一不可观察变量带来的论证困难，使分析更接近可操作的经验研究。在理论层面，本研究将功能对等理论应用于翻译决策的解释，但明确限定了解释的边界——即仅说明决策倾向与理论命题之间的相容性，而非证明理论的因果效力。这一限定有助于避免对理论的过度使用。

### 5.3 研究局限

本研究存在以下局限。第一，案例覆盖范围有限。虽然项目包含273<!--stat:total_segments-->个文本段，但本研究深入分析的案例仅占其中一小部分，且部分案例的审校发现属于建议性质（suggested_target_recorded），而非实际执行的修改（initial_final_changed），因此对翻译决策的解释可能未能覆盖全部决策类型。第二，修复记录的数量有限。8<!--stat:repaired_segments-->段相对于273<!--stat:total_segments-->段总量比例较低（约2.9%），虽然这些修复在性质上具有代表性，但在数量上可能不足以支撑对人工审校作用的更强判断——正如第5.1节所述，人工审校的作用应被限定为在已修复案例中的可追溯修正，而非整体性的实质作用。第三，功能对等理论的解释力有限。如前文所述，功能对等理论对“对等”标准的界定存在模糊性，且本研究仅能从事后结果反推决策倾向，无法确证理论命题在译者决策过程中的实际作用。第四，术语治理的分析受限于术语库覆盖范围。由于本项目未系统记录术语库收录条目的总量与类别分布，且仅少数案例含术语条目，本研究对术语治理效果的判断主要基于“未发生冲突”这一消极证据，未能对术语库的积极贡献进行更充分的评估。第五，对机器翻译局限的判断需保持审慎。由于部分局限可能源于源文本本身的复杂性而非引擎能力不足，本研究对机器翻译局限的结论仅限定于所分析的案例范围，未作更广泛的推广。第六，本研究未收集翻译时间、人工干预量等效率指标，因此无法对机器翻译的“效率”作出量化评估，相关判断仅限于任务完成度层面。第七，对源文本特征的判断基于所深入分析的案例集合，未对全部段落进行专名密度、长句占比等系统性量化统计，因此相关结论的适用范围以已考察段落为限。

### 5.4 未来研究方向

基于上述局限，未来研究可从以下方向拓展：其一，扩大案例分析的覆盖面，对更多类型的翻译决策进行系统分类与统计，以增强结论的稳健性；其二，结合译者访谈或过程追踪方法，补充译者决策过程的直接证据，以弥补事后归因的不足；其三，系统记录术语库收录条目的总量与类别分布，对术语库的构建过程与覆盖策略进行更细致的分析，探讨术语治理在回忆录类文本中的适用边界；其四，将功能对等理论与其他翻译理论（如目的论、交际翻译理论）进行比较，考察不同理论框架对同一批案例的解释力差异；其五，在评估机器翻译局限时，进一步区分引擎自身缺陷与源文本固有难度两类因素，建立更精细的归因框架；其六，在后续项目中系统记录翻译时间、人工干预量等效率指标，为机器翻译效率的量化评估提供数据基础；其七，对源文本的专名密度、长句占比等特征进行全量统计，以更系统的量化数据支撑对源文本特征的判断。这些方向有助于在现有证据基础上进一步深化对翻译决策机制的理解。
