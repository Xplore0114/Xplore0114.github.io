---
layout:     post
title:      "ReAct 拆解：ICLR 2023 论文怎么用一个循环定义 agent 范式"
subtitle:   "从结构解剖视角读一篇开山之作"
date:       2026-09-03
author:     "Kevin"
header-img: "img/post-bg-2015.jpg"
catalog:    true
section:    论文拆解
tags:
    - LLM
    - 智能体
    - 论文拆解
---

> 拆解对象：ReAct: Synergizing Reasoning and Acting in Language Models，ICLR 2023（notable top-5%）。作者来自普林斯顿大学与 Google Research Brain，一作 Shunyu Yao，后来也是 Tree of Thoughts、SWE-bench、SWE-agent 的核心作者。这篇文章只做一件事：分析这篇论文的结构为什么好。所有数字出自论文 arXiv 最新版正文，可对照原表复核。

## 一、为什么值得拆

agent 方向几乎所有后续工作的骨架都长在 ReAct 上：thought、action、observation 三者交错的单个循环，从 ChatGPT 插件时代的工具调用，到 Search-R1 的推理中搜索，再到今天各家 agent 框架的执行器，底层都是它。WebRL 在 WebArena 上评测的基线 agent 是它，Reflexion 的 Actor 直接复用它。

一个「交错生成」的极简设计撑起一个研究方向，这种论文天然是结构范本：方法只有一节，说服力全部来自实验的组织方式。

## 二、正文六节的骨架

| 章节 | 职责 | 拆解要点 |
| --- | --- | --- |
| 1 Introduction | 立论 | Figure 1 四格对比，一图讲完方法本质 |
| 2 ReAct | 方法 | 无小节，只占两页，含四大特性列举 |
| 3 Knowledge-Intensive Reasoning Tasks | 实验上半场 | HotpotQA / FEVER，自带 setup / methods / results |
| 4 Decision Making Tasks | 实验下半场 | ALFWorld / WebShop，结构与上半场对称 |
| 5 Related Work | 定位 | 后置到第 5 节，双线回顾后亮出与 SayCan、Inner Monologue 的差异 |
| 6 Conclusion | 收束 | 半页 |

两个结构决策值得注意。其一，相关工作后置：方法足够直观时，先让读者看懂再看谱系，阅读阻力最小。其二，实验按任务类型切成对称的两半，分别回答「推理任务上推理能否帮行动」与「决策任务上推理能否帮行动」，两半合起来才支撑标题里的 Synergizing 一词。

## 三、一张图立论：Figure 1 的四格对比

Introduction 用同一道 HotpotQA 题目跑了四种提示：Standard 直接答、CoT 只推理、Act 只行动、ReAct 交错。读者在见到任何公式之前，已经用肉眼看到了差异从哪来：Act-only 会盲目搜索，CoT 会顺着错误记忆编下去，ReAct 每一步行动前都有一次对观察的消化。

方法节顺理成章只需要做一件事：把动作空间扩展为 A ∪ L，语言空间 L 中的 thought 有六种用途（分解目标、注入常识、提取关键信息、跟踪进度、处理异常、合成答案）。方法本身越简单，写作的功夫越要花在「让读者第一眼就懂」上，Figure 1 承担了这个职能。

## 四、失败模式分析：Table 2 是被低估的宝藏

基于 200 个人工标注样本，ReAct 与 CoT 的成败模式被摆到同一张表里：

| 模式 | ReAct | CoT |
| --- | --- | --- |
| 成功案例中的幻觉（假阳性） | 6% | 14% |
| 失败中源于幻觉的占比 | 0% | 56% |
| 失败中的推理错误 | 47% | 16% |
| 搜索结果无信息（ReAct 特有） | 23% | 无此项 |

这张表诚实到报出自己的软肋：ReAct 的结构约束导致推理错误率反而更高，还会重复生成先前的动作。但正是这份诚实的分析直接催生了全文最佳结果：既然 ReAct 赢在事实性、CoT 赢在灵活性，那就组合，ReAct 与 CoT-SC 的混合提示在 HotpotQA 拿到 35.1 EM，在 FEVER 拿到 64.6，比任一单打都高。

失败分析写到位，会自己长出下一步的方案，这是实验设计的复利。

## 五、两组关键数字的组织方式

知识密集任务上，ReAct 在 HotpotQA（27.4 EM）其实略输 CoT（29.4），论文没有回避，而是把叙述重心放在「推理与行动各自的长处」上。决策任务上则是压倒性胜利：ALFWorld 71% 对模仿学习基线 BUTLER 的 37%，WebShop 成功率 40.0% 对 IL+RL 的 28.7%，而 ReAct 只用了 1 到 2 个 in-context 示例，对手用了 10³ 到 10⁵ 条训练轨迹。

最后一块拼图是微调闭环：仅用 3,000 条 ReAct 生成的正确轨迹微调，PaLM-8B 超过所有 PaLM-62B 提示方法，62B 超过所有 540B 提示方法。3.2 节埋下的「内外知识结合」线索，在 Figure 3 的 scaling 曲线上收口，前后呼应。

## 六、能学走的三个写作技巧

1. **一图立论**：Figure 1 用同一道题对比四种提示，方法的差异化主张在 Introduction 就完成论证，后面全部是证据
2. **双任务族对称实验**：知识密集与决策各占一节，结构对称，合起来支撑「通用」主张，单边实验撑不起 Synergizing
3. **Prompt 全部下沉附录 C**：正文保持干净，四套完整提示模板照抄即可复现，可复现承诺由附录兑现

## 尾注：对我自己工作的映射

ReAct 的 thought 六种用途，几乎就是赛后教练系统「行为诊断 → 时间归因」环节的提示词骨架：从观察里提取关键信息、跟踪任务进度、异常时调整计划。而 Table 2 的幻觉率对比（6% 对 14%）从另一个方向印证了 OKC-SFT 的结论：让推理过程有外部证据可依，幻觉率就能被系统性压下来（我们从 34.4% 压到 15.6%）。算法层输出结构化证据，LLM 层的每一步 thought 都有据可查，这与 ReAct 让每个 answer 前都有 observation 是同一件事。

## 参考

- 论文：arXiv:2210.03629，发表于 ICLR 2023（notable top-5%）
- 代码与提示模板：github.com/ysymyth/ReAct
- 主实验口径：HotpotQA 与 FEVER 为知识密集任务（PaLM-540B 提示），ALFWorld 与 WebShop 为决策任务（best of 6 与单次评测）
