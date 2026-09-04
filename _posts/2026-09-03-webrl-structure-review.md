---
layout:     post
title:      "WebRL 拆解：ICLR 2025 论文怎么把自进化课程讲成闭环"
subtitle:   "从结构解剖视角读一篇 web agent 强化学习论文"
date:       2026-09-03
author:     "Kevin"
header-img: "img/post-bg-2015.jpg"
catalog:    true
section:    论文拆解
tags:
    - LLM
    - 强化学习
    - Agent
    - 论文拆解
---

> 拆解对象：WebRL: Training LLM Web Agents via Self-Evolving Online Curriculum Reinforcement Learning，ICLR 2025。作者来自清华大学与智谱 AI，开源代码在 THUDM/WebRL。与上一篇拆 Search-R1 一样，这里只分析结构为什么好，数字全部出自论文 arXiv 最新版，可对照原表复核。

## 一、问题定义：三重困境的一次性陈述

开源模型当 web agent，Introduction 一次点名三个困境：

1. **任务稀缺**：WebArena-Lite 这类环境训练任务有限，静态数据很快学完
2. **反馈稀疏**：只有任务终局成败信号，没有逐步奖励
3. **分布漂移**：在线学习与课程推进会让策略失稳，学到的新能力覆盖旧能力

方法节随后按这三件事逐一给出组件，挑战与组件一一映射。这是这篇论文结构上最值得学的骨架。

## 二、结构上的反常规：Related Works 放在第 4 节

NLP 会议论文的常见排布是 Related Works 紧跟 Introduction；WebRL 把它放到实验之后、结论之前。好处直接可见：Introduction 末尾紧接方法总览图（Figure 2），读者从「痛点」到「方案」零距离，第一遍阅读不需要先穿越十篇引用。ML 系会议对这种排布接受度高，投稿时可以主动利用这个惯例差异。

## 三、三挑战与三组件的映射

| 挑战 | 组件 | 结构位置 | 专属验证 |
| --- | --- | --- | --- |
| 任务稀缺 | 自进化课程：失败任务生成器 + critic 难度过滤 | 2.1 | 3.9 案例分析 |
| 反馈稀疏 | ORM（outcome-supervised reward model） | 2 正文 | 3.8 ORM 单独评估 |
| 分布漂移 | KL 约束 + 经验回放 + 困惑度过滤 | 2.2 | 3.7 消融 |

每个组件在实验节都有专属小节单独检验，方法与实验完全对称。组件可独立拆装的结构，让审稿人能逐项确认贡献，也方便后续工作单独引用其中一件。

三个组件的关键设计：

1. **自进化课程**：以上一阶段失败的指令为种子做 in-breadth 扩展生成新任务；critic 结合初始状态打分，只保留 0.05 到 0.75 区间的指令，保证任务可行且难度匹配当前能力；再用 GPT-4o 自动排除环境中根本不可完成的任务
2. **ORM**：一个 LLM 奖励模型，比较输出 YES 与 NO 的概率给出二元判定，输入为指令、历史动作与最终状态 HTML。测试集精度 80.8%，高于 GPT-4 的 71.9% 与 GPT-4V 的 71.2%
3. **策略更新**：带 KL 约束与熵正则的最大熵 RL 目标，off-policy 损失 L = E[(β log(πθ/πref) − A*)²]；经验回放只存成功轨迹，并用上一阶段 actor 的困惑度过滤，区间 [1/0.95, 1/0.5] 的动作最优（该区间平均成功率 31.5%，两侧区间分别只有 29.1% 与 23.0%）

<figure style="margin:28px 0">
<svg viewBox="0 0 680 336" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs><marker id="wr-a" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#57606a"/></marker></defs>
  <rect x="50" y="36" width="190" height="76" rx="10" fill="#f2fafd" stroke="#56B4E9" stroke-width="1.5"/>
  <text x="145" y="62" text-anchor="middle" font-size="13" font-weight="700" fill="#1E88B8">Actor（阶段 t）</text>
  <text x="145" y="84" text-anchor="middle" font-size="10.5" fill="#57606a">在当前课程任务上</text>
  <text x="145" y="100" text-anchor="middle" font-size="10.5" fill="#57606a">执行 web 轨迹</text>
  <rect x="440" y="36" width="190" height="76" rx="10" fill="#fdf8ef" stroke="#E69F00" stroke-width="1.5"/>
  <text x="535" y="62" text-anchor="middle" font-size="13" font-weight="700" fill="#B77500">ORM 奖励模型</text>
  <text x="535" y="84" text-anchor="middle" font-size="10.5" fill="#57606a">P(YES)/P(NO) 二元判定</text>
  <text x="535" y="100" text-anchor="middle" font-size="10.5" fill="#57606a">精度 80.8% &gt; GPT-4 71.9%</text>
  <rect x="440" y="196" width="190" height="92" rx="10" fill="#f2fbf7" stroke="#009E73" stroke-width="1.5"/>
  <text x="535" y="222" text-anchor="middle" font-size="13" font-weight="700" fill="#00805C">课程进化器</text>
  <text x="535" y="244" text-anchor="middle" font-size="10.5" fill="#57606a">失败指令做种子 in-breadth 扩展</text>
  <text x="535" y="260" text-anchor="middle" font-size="10.5" fill="#57606a">critic 难度过滤 [0.05, 0.75]</text>
  <text x="535" y="276" text-anchor="middle" font-size="10.5" fill="#57606a">GPT-4o 排除不可完成任务</text>
  <rect x="50" y="196" width="190" height="92" rx="10" fill="#faf3f7" stroke="#CC79A7" stroke-width="1.5"/>
  <text x="145" y="222" text-anchor="middle" font-size="13" font-weight="700" fill="#A05177">策略更新</text>
  <text x="145" y="244" text-anchor="middle" font-size="10.5" fill="#57606a">KL 约束 + 熵正则</text>
  <text x="145" y="260" text-anchor="middle" font-size="10.5" fill="#57606a">经验回放只存成功轨迹</text>
  <text x="145" y="276" text-anchor="middle" font-size="10.5" fill="#57606a">困惑度过滤 [1/0.95, 1/0.5]</text>
  <path d="M 240 70 C 340 70, 350 70, 435 70" fill="none" stroke="#57606a" stroke-width="1.4" marker-end="url(#wr-a)"/>
  <text x="337" y="60" text-anchor="middle" font-size="10.5" fill="#57606a">轨迹 + 终态 HTML</text>
  <path d="M 535 112 C 535 150, 535 160, 535 191" fill="none" stroke="#57606a" stroke-width="1.4" marker-end="url(#wr-a)"/>
  <text x="600" y="155" text-anchor="middle" font-size="10.5" fill="#B77500">失败任务</text>
  <path d="M 435 242 C 300 242, 280 242, 246 242" fill="none" stroke="#57606a" stroke-width="1.4" marker-end="url(#wr-a)"/>
  <text x="340" y="232" text-anchor="middle" font-size="10.5" fill="#00805C">新课程（阶段 t+1）</text>
  <path d="M 145 191 C 145 155, 145 150, 145 117" fill="none" stroke="#CC79A7" stroke-width="1.6" stroke-dasharray="6 4" marker-end="url(#wr-a)"/>
  <text x="145" y="160" text-anchor="middle" font-size="10.5" fill="#A05177">更新后的 actor</text>
  <path d="M 440 100 C 330 100, 300 130, 246 168" fill="none" stroke="#CC79A7" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#wr-a)"/>
  <text x="310" y="140" text-anchor="middle" font-size="10" fill="#A05177">成功轨迹入回放</text>
  <text x="340" y="146" text-anchor="middle" font-size="12" font-weight="600" fill="#24292f">自进化闭环</text>
  <text x="340" y="316" text-anchor="middle" font-size="10.5" fill="#8b949e">Figure 2 仿绘：任务从失败里长出来，难度随能力外推；三挑战（任务稀缺 / 反馈稀疏 / 分布漂移）各有专属组件与专属验证小节</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">自进化课程闭环仿绘：失败任务生成新课程，ORM 提供稠密判定，KL 约束与回放防漂移</figcaption>
</figure>


## 四、实验节的分析链：从主结果到单组件验证

实验节 9 个小节是一条三层递进的链：

| 层次 | 小节 | 作用 |
| --- | --- | --- |
| 整体有效 | 3.1 环境与基线、3.2 主结果、3.3 规模效应 | WebArena-Lite 165 个测试用例，三个基座全面超越基线 |
| 机制解释 | 3.4 错误类型分布、3.5 步骤数分层、3.6 复杂度分层 | 解释「为什么有效」：大幅减少中途卡死的循环错误，长步骤与高复杂度任务优势最大 |
| 组件检验 | 3.7 消融、3.8 ORM 评估、3.9 案例 | 把每个组件拆出来单独验证 |

消融的四个变体设计得干净：去掉 replay buffer、去掉 KL 约束、两者都去掉、去掉课程学习，每次只动一个部件。结论各自成立：无 buffer 性能随时间恶化，KL 约束一致优于 REINFORCE 式更新，去掉课程则上限更低。

## 五、开场图直接立论

Figure 1 放在 Introduction：专有模型与开源模型的成功率对比，WebRL 训练后的 GLM-4 与 Llama 站在最右，GPT-4-Turbo 的 17.6% 被压在下方。摘要里的关键数字全部浓缩在这张图里：

| 模型 | WebArena-Lite 成功率 |
| --- | --- |
| Llama-3.1-8B（训练前 → 后） | 4.8% → 42.4% |
| GLM-4-9B（训练前 → 后） | 6.1% → 43.0% |
| Llama-3.1-70B（训练前 → 后） | 12.7% → 49.1% |
| 同基座 8B 用 SFT | 20.6% |
| GPT-4-Turbo / GPT-4o | 17.6% / 13.9% |
| 此前开源最优 AutoWebGLM | 18.2% |

相比 GPT-4-Turbo 相对提升超过 160%。读论文的人扫一眼图就知道主张是什么，这种「开场即结论」的图值得优先设计。

<figure style="margin:28px 0">
<svg viewBox="0 0 680 316" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs><marker id="wf-a" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#57606a"/></marker></defs>
  <g stroke="#eaeef2"><line x1="170" y1="40" x2="640" y2="40"/><line x1="170" y1="96" x2="640" y2="96"/><line x1="170" y1="152" x2="640" y2="152"/><line x1="170" y1="208" x2="640" y2="208"/><line x1="170" y1="264" x2="640" y2="264"/></g>
  <line x1="170" y1="270" x2="640" y2="270" stroke="#d0d7de"/>
  <g font-size="10.5" fill="#8b949e"><text x="164" y="274" text-anchor="end">0</text><text x="164" y="218" text-anchor="end">10</text><text x="164" y="162" text-anchor="end">20</text><text x="164" y="106" text-anchor="end">30</text><text x="164" y="50" text-anchor="end">40</text></g>
  <g font-size="11.5" fill="#24292f" text-anchor="end">
    <text x="162" y="62">GPT-4o</text>
    <text x="162" y="90">GPT-4-Turbo</text>
    <text x="162" y="112">AutoWebGLM</text>
    <text x="162" y="126" font-size="9" fill="#8b949e">此前开源最优</text>
    <text x="162" y="146">同基座 8B · SFT</text>
    <text x="162" y="185">Llama-3.1-8B</text>
    <text x="162" y="229">GLM-4-9B</text>
    <text x="162" y="262">Llama-3.1-70B</text>
  </g>
  <g>
    <rect x="170" y="48" width="134" height="16" rx="4" fill="#8b949e"/><text x="312" y="61" font-size="11" fill="#57606a">13.9%</text>
    <rect x="170" y="76" width="170" height="16" rx="4" fill="#8b949e"/><text x="348" y="89" font-size="11" fill="#57606a">17.6%</text>
    <rect x="170" y="104" width="175" height="16" rx="4" fill="#8b949e"/><text x="353" y="117" font-size="11" fill="#57606a">18.2%</text>
    <rect x="170" y="132" width="198" height="16" rx="4" fill="#E69F00"/><text x="376" y="145" font-size="11" fill="#B77500">20.6%</text>
    <rect x="170" y="170" width="46" height="16" rx="4" fill="#c9d1d9"/><text x="224" y="183" font-size="10.5" fill="#8b949e">4.8%</text>
    <path d="M 228 178 L 280 178" stroke="#009E73" stroke-width="1.4" marker-end="url(#wf-a)"/>
    <rect x="286" y="170" width="238" height="16" rx="4" fill="#009E73"/><text x="532" y="183" font-size="11.5" font-weight="700" fill="#00805C">42.4%</text>
    <rect x="170" y="214" width="59" height="16" rx="4" fill="#c9d1d9"/><text x="237" y="227" font-size="10.5" fill="#8b949e">6.1%</text>
    <path d="M 241 222 L 293 222" stroke="#009E73" stroke-width="1.4" marker-end="url(#wf-a)"/>
    <rect x="299" y="214" width="242" height="16" rx="4" fill="#009E73"/><text x="549" y="227" font-size="11.5" font-weight="700" fill="#00805C">43.0%</text>
    <rect x="170" y="247" width="122" height="16" rx="4" fill="#c9d1d9"/><text x="300" y="260" font-size="10.5" fill="#8b949e">12.7%</text>
    <path d="M 304 255 L 356 255" stroke="#009E73" stroke-width="1.4" marker-end="url(#wf-a)"/>
    <rect x="362" y="247" width="276" height="16" rx="4" fill="#009E73"/><text x="646" y="260" font-size="11.5" font-weight="700" fill="#00805C">49.1%</text>
  </g>
  <g font-size="10.5" fill="#8b949e">
    <rect x="420" y="30" width="12" height="10" rx="2" fill="#c9d1d9"/><text x="438" y="39">WebRL 训练前</text>
    <rect x="530" y="30" width="12" height="10" rx="2" fill="#009E73"/><text x="548" y="39">WebRL 训练后</text>
  </g>
  <text x="405" y="298" font-size="10.5" fill="#8b949e" text-anchor="middle">Figure 1 仿绘 · WebArena-Lite 165 测试用例成功率（%）· 8B 相对 GPT-4-Turbo 提升超 160%</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">Figure 1 仿绘：训练前后同基座对比让「开源反超专有」的主张一眼可读，灰色小条是训练前的起点</figcaption>
</figure>


## 六、能学走的三个技巧

1. **挑战、组件、验证三点映射**：方法节每个小节在实验节都有对偶小节，审稿人核对贡献时不用自己拼图
2. **消融设计成独立可拆的变体**：每个变体只去掉一个部件，任何一条结论都能被单独引用
3. **附录三段式论证方法合法性**：附录 A 依次给推导（A.1）、理论证明（A.2）、与 DPO/PPO/AWR 的特性对比表（A.3 Table 4），把「这个更新规则凭什么成立」的完整论证后置，正文保持轻装

## 尾注：对我自己工作的映射

自进化课程的实质是从失败里长出训练任务：失败指令做种子，critic 卡难度区间，任务难度随能力外推。做 QQ 飞车赛后教练的 Phase 0 数据可行性验证时，这个思路有直接参考价值：冷启动数据不足的场景，任务的「生成与过滤」流水线本身可以成为数据建设的一部分，让训练集随模型能力一起生长。

## 参考

- 论文：arXiv:2411.02337，发表于 ICLR 2025（Poster）
- 代码：github.com/THUDM/WebRL
- OpenReview：forum?id=oVKEAFjEqv
