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

<figure style="margin:28px 0">
<svg viewBox="0 0 680 318" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs><marker id="ra-a" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#57606a"/></marker></defs>
  <rect x="8" y="30" width="152" height="278" rx="10" fill="#f6f8fa" stroke="#d0d7de"/>
  <rect x="176" y="30" width="152" height="278" rx="10" fill="#fdf8ef" stroke="#E69F00" stroke-opacity=".45"/>
  <rect x="344" y="30" width="152" height="278" rx="10" fill="#f2fafd" stroke="#56B4E9" stroke-opacity=".55"/>
  <rect x="512" y="30" width="152" height="278" rx="10" fill="#f2fbf7" stroke="#009E73" stroke-opacity=".55"/>
  <text x="84" y="20" text-anchor="middle" font-size="12.5" font-weight="700" fill="#57606a">Standard 直接答</text>
  <text x="252" y="20" text-anchor="middle" font-size="12.5" font-weight="700" fill="#B77500">CoT 只推理</text>
  <text x="420" y="20" text-anchor="middle" font-size="12.5" font-weight="700" fill="#1E88B8">Act 只行动</text>
  <text x="588" y="20" text-anchor="middle" font-size="12.5" font-weight="700" fill="#00805C">ReAct 交错</text>
  <g font-size="11" text-anchor="middle">
    <rect x="22" y="46" width="124" height="26" rx="6" fill="#fff" stroke="#d0d7de"/><text x="84" y="63" fill="#24292f">问题</text>
    <line x1="84" y1="72" x2="84" y2="86" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="22" y="88" width="124" height="26" rx="6" fill="#fff" stroke="#d0d7de"/><text x="84" y="105" fill="#24292f">直接作答</text>
    <text x="84" y="138" font-size="10.5" fill="#9a6700">⚠ 无外部证据</text>
    <text x="84" y="154" font-size="10.5" fill="#8b949e">赌模型记忆</text>
    <rect x="190" y="46" width="124" height="26" rx="6" fill="#fff" stroke="#E69F00"/><text x="252" y="63" fill="#24292f">问题</text>
    <line x1="252" y1="72" x2="252" y2="86" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="190" y="88" width="124" height="26" rx="6" fill="#fff" stroke="#E69F00"/><text x="252" y="105" fill="#24292f">思考 · 思考 · …</text>
    <line x1="252" y1="114" x2="252" y2="128" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="190" y="130" width="124" height="26" rx="6" fill="#fff" stroke="#E69F00"/><text x="252" y="147" fill="#24292f">作答（编造）</text>
    <text x="252" y="180" font-size="10.5" fill="#9a6700">⚠ 顺错误记忆编下去</text>
    <text x="252" y="196" font-size="10.5" fill="#8b949e">失败中 56% 源于幻觉</text>
    <rect x="358" y="46" width="124" height="26" rx="6" fill="#fff" stroke="#56B4E9"/><text x="420" y="63" fill="#24292f">问题</text>
    <line x1="420" y1="72" x2="420" y2="86" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="358" y="88" width="124" height="26" rx="6" fill="#fff" stroke="#56B4E9"/><text x="420" y="105" fill="#24292f">Search(A)</text>
    <line x1="420" y1="114" x2="420" y2="128" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="358" y="130" width="124" height="26" rx="6" fill="#fff" stroke="#56B4E9"/><text x="420" y="147" fill="#24292f">Search(B)</text>
    <line x1="420" y1="156" x2="420" y2="170" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="358" y="172" width="124" height="26" rx="6" fill="#fff" stroke="#56B4E9"/><text x="420" y="189" fill="#24292f">Search(A) 重复</text>
    <text x="420" y="222" font-size="10.5" fill="#9a6700">⚠ 盲目搜索</text>
    <text x="420" y="238" font-size="10.5" fill="#8b949e">23% 搜索无信息</text>
    <rect x="526" y="46" width="124" height="24" rx="6" fill="#fff" stroke="#d0d7de"/><text x="588" y="62" fill="#24292f">问题</text>
    <line x1="588" y1="70" x2="588" y2="80" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="526" y="82" width="124" height="24" rx="6" fill="#eafaf4" stroke="#009E73"/><text x="588" y="98" fill="#005C42" font-weight="600">思考：还缺什么</text>
    <line x1="588" y1="106" x2="588" y2="116" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="526" y="118" width="124" height="24" rx="6" fill="#fff" stroke="#56B4E9"/><text x="588" y="134" fill="#24292f">行动：Search</text>
    <line x1="588" y1="142" x2="588" y2="152" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="526" y="154" width="124" height="24" rx="6" fill="#f2fafd" stroke="#8ba9b8"/><text x="588" y="170" fill="#3d5666">观察：返回结果</text>
    <line x1="588" y1="178" x2="588" y2="188" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="526" y="190" width="124" height="24" rx="6" fill="#eafaf4" stroke="#009E73"/><text x="588" y="206" fill="#005C42" font-weight="600">思考：消化证据</text>
    <line x1="588" y1="214" x2="588" y2="224" stroke="#57606a" stroke-width="1.3" marker-end="url(#ra-a)"/>
    <rect x="526" y="226" width="124" height="24" rx="6" fill="#fff" stroke="#009E73" stroke-width="1.6"/><text x="588" y="242" fill="#24292f" font-weight="600">作答 ✓</text>
    <text x="588" y="272" font-size="10.5" fill="#00805C">每个 answer 前</text>
    <text x="588" y="288" font-size="10.5" fill="#00805C">都有 observation</text>
  </g>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">Figure 1 四格对比仿绘：同一道 HotpotQA 题目下四种提示策略的行为差异（数字出自正文 Table 2）</figcaption>
</figure>

方法节顺理成章只需要做一件事：把动作空间扩展为 A ∪ L，语言空间 L 中的 thought 有六种用途（分解目标、注入常识、提取关键信息、跟踪进度、处理异常、合成答案）。方法本身越简单，写作的功夫越要花在「让读者第一眼就懂」上，Figure 1 承担了这个职能。

## 四、失败模式分析：Table 2 是被低估的宝藏

基于 200 个人工标注样本，ReAct 与 CoT 的成败模式被摆到同一张表里：

| 模式 | ReAct | CoT |
| --- | --- | --- |
| 成功案例中的幻觉（假阳性） | 6% | 14% |
| 失败中源于幻觉的占比 | 0% | 56% |
| 失败中的推理错误 | 47% | 16% |
| 搜索结果无信息（ReAct 特有） | 23% | 无此项 |

<figure style="margin:28px 0">
<svg viewBox="0 0 680 248" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <rect x="150" y="40" width="14" height="12" rx="2" fill="#009E73"/><text x="170" y="50" font-size="11.5" fill="#57606a">ReAct</text>
  <rect x="230" y="40" width="14" height="12" rx="2" fill="#E69F00"/><text x="250" y="50" font-size="11.5" fill="#57606a">CoT</text>
  <g font-size="12" fill="#24292f">
    <text x="140" y="87" text-anchor="end">成功中的幻觉</text>
    <text x="140" y="119" text-anchor="end">失败中源于幻觉</text>
    <text x="140" y="151" text-anchor="end">失败中的推理错误</text>
    <text x="140" y="183" text-anchor="end">搜索结果无信息</text>
  </g>
  <line x1="150" y1="196" x2="590" y2="196" stroke="#d0d7de"/>
  <g>
    <rect x="150" y="76" width="40" height="13" rx="3" fill="#009E73"/><text x="196" y="87" font-size="11" fill="#57606a">6%</text>
    <rect x="150" y="91" width="93" height="13" rx="3" fill="#E69F00"/><text x="249" y="102" font-size="11" fill="#57606a">14%</text>
    <rect x="150" y="122" width="2" height="13" rx="1" fill="#009E73"/><text x="160" y="133" font-size="11" fill="#57606a">0%</text>
    <rect x="150" y="137" width="373" height="13" rx="3" fill="#E69F00"/><text x="529" y="148" font-size="11" fill="#57606a">56%</text>
    <rect x="150" y="168" width="313" height="13" rx="3" fill="#009E73"/><text x="469" y="179" font-size="11" fill="#57606a">47%</text>
    <rect x="150" y="183" width="107" height="13" rx="3" fill="#E69F00"/><text x="263" y="194" font-size="11" fill="#57606a">16%</text>
  </g>
  <text x="590" y="225" font-size="10.5" fill="#8b949e" text-anchor="end">ReAct 特有项：搜索无信息 23%（CoT 无此行为）· 比例尺 0–60%</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">Table 2 数据重绘：ReAct 用更高的推理错误率换来了幻觉的系统性下降，混合两者因此拿到最佳结果</figcaption>
</figure>

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
