---
layout:     post
title:      "DAPO 拆解：怎么用四个机制把 GRPO 在 AIME 2024 从 30 分拉到 50 分"
subtitle:   "从结构解剖视角读一篇开源 RL 系统的工程复盘"
date:       2026-09-03
author:     "Kevin"
header-img: "img/post-bg-digital-native.jpg"
catalog:    true
section:    论文拆解
tags:
    - LLM
    - 强化学习
    - 论文拆解
---

> 拆解对象：DAPO: An Open-Source LLM Reinforcement Learning System at Scale（arXiv:2503.14476 v2，2025-03-17 投稿，2025-05-20 修订），目前为预印本，尚未在顶会正式录用（dblp 仅收录为 arXiv）。作者来自 ByteDance Seed、清华大学 AIR、香港大学、SIA-Lab，通讯作者 Qiying Yu。这篇文章只做一件事：分析这篇论文的结构为什么好。所有数字与公式来自 arXiv v2 正文与附录 A，可对照原表复核。

## 一、为什么值得拆

R1 之后，社区复现 GRPO 时普遍踩到三件事：熵坍缩、奖励信号噪声、训练不稳定。DeepSeek 的技术报告里没讲怎么做，但 DAPO 把「该怎么做」一次性给了出来。它在 Qwen2.5-32B base 上把 AIME 2024 从 GRPO 的 30 分拉到 50 分，超过 DeepSeek-R1-Zero-Qwen-32B 的 47 分，只用了一半的训练步数；同时把训练代码 verl、数据集 DAPO-Math-17k、模型权重全部开源。

这篇文章的拆解价值在于「四个机制全部沉在 GRPO 之外」，证明 R1 之后的下一波进展不在新算法，而在对 GRPO 失败模式的精确归因与逐条修复。这是工程复盘型论文的范本，对想自己跑 R1 复现的人尤其重要。

## 二、正文骨架：六节里只有一节讲方法

| 章节 | 职责 | 拆解要点 |
| --- | --- | --- |
| 1 Introduction | 立论 | 「R1/Z1 报告里关键训练细节没写」一句话立论，naive GRPO 在 32B 上只跑出 30 分，与 DeepSeek-R1 公开的 47 分存在明显差距 |
| 2 Preliminary | 铺垫 | 2.1 PPO、2.2 GRPO 两个核心公式，每个一段就讲清楚，避免与正文方法混淆 |
| 3 DAPO Algorithm | 方法主体 | 四个机制按依赖序展开（下节详述） |
| 4 Experiments | 主实验 | Table 1 是渐进式消融，AIME 24/25/LLM 20 各自一张主表 |
| 5 Discussion | 讨论 | 四个机制各自的失败模式与潜在改进方向 |
| 6 Conclusions | 收束 | 一页以内 |

正文只有六节，把所有可复现工程细节（训练细节、对比基线、reward 设计、prompt 模板、硬件配置）沉到附录 A。方法论文的核心资产是「机制归因 + 消融证据」，验证性内容一律后置。

## 三、四个机制的依赖序

第 3 节给出四个机制，作者在公式与正文中严格按「先消熵坍缩、再压梯度噪声、再控响应长度、再稳截断奖励」的顺序排布：

| 机制 | 作用对象 | 关键设计 |
| --- | --- | --- |
| Clip-Higher | PPO/GRPO 的对称裁剪区间 | 改成非对称 `[1-ε_low, 1+ε_high]`，取 `ε_low = 0.2`、`ε_high = 0.28`（Equation 10） |
| Dynamic Sampling | prompt 粒度 | 过采样后丢弃 accuracy 等于 0 与 1 的 prompt，保证批次内全部 prompt 都贡献有效梯度 |
| Token-Level Policy Gradient Loss | 损失归一化粒度 | 把 GRPO 的「先按序列内 token 平均、再按样本平均」改成直接按组内总 token 数归一化（Equation 12） |
| Overlong Reward Shaping | 超长截断样本 | Overlong Filtering 屏蔽截断样本的损失 + Soft Overlong Punishment 给长度惩罚；`L_max = 16,384`，`L_cache = 4,096`，最大生成长度 20,480（Equation 13） |

<figure style="margin:28px 0">
<svg viewBox="0 0 680 268" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs><marker id="dp-a" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#57606a"/></marker></defs>
  <text x="340" y="18" text-anchor="middle" font-size="11.5" fill="#8b949e">GRPO 的故障模式（上）→ DAPO 的逐条修复（下），顺序即依赖序</text>
  <g font-size="11" text-anchor="middle">
    <rect x="16" y="34" width="150" height="46" rx="8" fill="#fdf3f1" stroke="#D55E00" stroke-opacity=".5"/>
    <text x="91" y="54" font-size="11.5" font-weight="700" fill="#A0410A">熵坍缩</text>
    <text x="91" y="71" fill="#8b5a4a">探索 token 概率被压死</text>
    <line x1="91" y1="80" x2="91" y2="98" stroke="#57606a" stroke-width="1.3" marker-end="url(#dp-a)"/>
    <rect x="16" y="100" width="150" height="58" rx="8" fill="#f2fbf7" stroke="#009E73" stroke-width="1.4"/>
    <text x="91" y="121" font-size="12" font-weight="700" fill="#00805C">Clip-Higher</text>
    <text x="91" y="138" fill="#57606a">非对称区间 [0.8, 1.28]</text>
    <text x="91" y="152" fill="#57606a">Eq.10 · 只放宽上界</text>
    <rect x="186" y="34" width="150" height="46" rx="8" fill="#fdf3f1" stroke="#D55E00" stroke-opacity=".5"/>
    <text x="261" y="54" font-size="11.5" font-weight="700" fill="#A0410A">全对 / 全错 prompt</text>
    <text x="261" y="71" fill="#8b5a4a">组内基线无区分度</text>
    <line x1="261" y1="80" x2="261" y2="98" stroke="#57606a" stroke-width="1.3" marker-end="url(#dp-a)"/>
    <rect x="186" y="100" width="150" height="58" rx="8" fill="#f2fbf7" stroke="#009E73" stroke-width="1.4"/>
    <text x="261" y="121" font-size="12" font-weight="700" fill="#00805C">Dynamic Sampling</text>
    <text x="261" y="138" fill="#57606a">过采样后丢弃 acc ∈ {0,1}</text>
    <text x="261" y="152" fill="#57606a">每个 prompt 贡献梯度</text>
    <rect x="356" y="34" width="150" height="46" rx="8" fill="#fdf3f1" stroke="#D55E00" stroke-opacity=".5"/>
    <text x="431" y="54" font-size="11.5" font-weight="700" fill="#A0410A">长序列梯度稀释</text>
    <text x="431" y="71" fill="#8b5a4a">短答案主导样本均值</text>
    <line x1="431" y1="80" x2="431" y2="98" stroke="#57606a" stroke-width="1.3" marker-end="url(#dp-a)"/>
    <rect x="356" y="100" width="150" height="58" rx="8" fill="#f2fbf7" stroke="#009E73" stroke-width="1.4"/>
    <text x="431" y="121" font-size="12" font-weight="700" fill="#00805C">Token-Level Loss</text>
    <text x="431" y="138" fill="#57606a">按组内总 token 数归一</text>
    <text x="431" y="152" fill="#57606a">Eq.12</text>
    <rect x="526" y="34" width="150" height="46" rx="8" fill="#fdf3f1" stroke="#D55E00" stroke-opacity=".5"/>
    <text x="601" y="54" font-size="11.5" font-weight="700" fill="#A0410A">截断样本被误罚</text>
    <text x="601" y="71" fill="#8b5a4a">合理推理吃到 0 奖励</text>
    <line x1="601" y1="80" x2="601" y2="98" stroke="#57606a" stroke-width="1.3" marker-end="url(#dp-a)"/>
    <rect x="526" y="100" width="150" height="58" rx="8" fill="#f2fbf7" stroke="#009E73" stroke-width="1.4"/>
    <text x="601" y="121" font-size="12" font-weight="700" fill="#00805C">Overlong Reward</text>
    <text x="601" y="138" fill="#57606a">Filtering + Soft 惩罚</text>
    <text x="601" y="152" fill="#57606a">L_max 16,384 · Eq.13</text>
  </g>
  <g>
    <line x1="91" y1="172" x2="586" y2="172" stroke="#d0d7de" stroke-dasharray="5 4"/>
    <path d="M 176 172 L 176 196" stroke="#57606a" stroke-width="1.2" marker-end="url(#dp-a)"/>
    <path d="M 346 172 L 346 196" stroke="#57606a" stroke-width="1.2" marker-end="url(#dp-a)"/>
    <path d="M 516 172 L 516 196" stroke="#57606a" stroke-width="1.2" marker-end="url(#dp-a)"/>
    <text x="340" y="216" text-anchor="middle" font-size="12" font-weight="700" fill="#24292f">Naive GRPO 30 分 → 完整 DAPO 50 分（AIME 2024，avg@32）</text>
    <text x="340" y="236" text-anchor="middle" font-size="10.5" fill="#8b949e">每格上方故障模式来自论文第 2 节的诊断，下方修复来自第 3 节的机制定义</text>
    <text x="340" y="256" text-anchor="middle" font-size="10.5" fill="#8b949e">虚线表示依赖关系：熵稳定后 Dynamic Sampling 才能挑出有效 prompt</text>
  </g>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">四个机制的依赖序仿绘：每个机制对应 GRPO 长链 CoT 训练下的一个具体故障模式</figcaption>
</figure>

Clip-Higher 是基础，先把熵抬起来才有探索空间；Dynamic Sampling 在熵稳定后才能真正挑出有效 prompt；Token-Level Loss 解决长序列梯度被稀释的问题；Overlong Reward Shaping 处理的是「被截断的合理推理不该被罚」这个奖励噪声。四个机制各自对应 GRPO 在长 CoT 训练下的一个具体故障模式，缺一项都会让训练曲线出现肉眼可见的退化。

非对称区间的选择细节也值得记一句：作者刻意不增大 `ε_low`，因为一旦放大下界会把低概率探索 token 的概率压向零，触发「采样空间坍缩」。Clip-Higher 的方向性是「向上放宽探索、向下保持谨慎」，这是一个反直觉但有解释的设计。

## 四、消融是累加式而非替换式

Table 1 是本文最值得读的一张表，因为它按累加方式呈现四个机制的贡献（替换式消融作参考）：

| 配置 | AIME 2024（avg@32） | 增量 |
| --- | --- | --- |
| DeepSeek-R1-Zero-Qwen-32B | 47 | 外部参考 |
| Naive GRPO | 30 | 基线 |
| + Overlong Filtering | 36 | +6 |
| + Clip-Higher | 38 | +2 |
| + Soft Overlong Punishment | 41 | +3 |
| + Token-level Loss | 42 | +1 |
| + Dynamic Sampling（完整 DAPO） | 50 | +8 |

<figure style="margin:28px 0">
<svg viewBox="0 0 680 292" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <g stroke="#eaeef2"><line x1="50" y1="230" x2="660" y2="230"/><line x1="50" y1="200" x2="660" y2="200"/><line x1="50" y1="170" x2="660" y2="170"/><line x1="50" y1="140" x2="660" y2="140"/><line x1="50" y1="110" x2="660" y2="110"/><line x1="50" y1="80" x2="660" y2="80"/></g>
  <g font-size="10.5" fill="#8b949e"><text x="44" y="234" text-anchor="end">25</text><text x="44" y="204" text-anchor="end">30</text><text x="44" y="174" text-anchor="end">35</text><text x="44" y="144" text-anchor="end">40</text><text x="44" y="114" text-anchor="end">45</text><text x="44" y="84" text-anchor="end">50</text></g>
  <line x1="50" y1="235" x2="660" y2="235" stroke="#d0d7de"/>
  <line x1="50" y1="98" x2="660" y2="98" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="6 4"/>
  <text x="654" y="92" font-size="10.5" fill="#8b949e" text-anchor="end">DeepSeek-R1-Zero-Qwen-32B = 47</text>
  <g>
    <rect x="80" y="200" width="72" height="30" rx="4" fill="#8b949e"/>
    <rect x="167" y="164" width="72" height="36" rx="4" fill="#E69F00"/>
    <rect x="254" y="152" width="72" height="12" rx="4" fill="#E69F00"/>
    <rect x="341" y="134" width="72" height="18" rx="4" fill="#E69F00"/>
    <rect x="428" y="128" width="72" height="6" rx="3" fill="#E69F00"/>
    <rect x="515" y="80" width="72" height="48" rx="4" fill="#009E73"/>
    <g font-size="11.5" font-weight="700" fill="#24292f" text-anchor="middle">
      <text x="116" y="194">30</text><text x="203" y="158">+6</text><text x="290" y="146">+2</text><text x="377" y="128">+3</text><text x="464" y="122">+1</text><text x="551" y="74" fill="#00805C">50</text>
    </g>
    <g font-size="10" fill="#57606a" text-anchor="middle">
      <text x="116" y="252">Naive</text><text x="116" y="265">GRPO</text>
      <text x="203" y="252">+ Overlong</text><text x="203" y="265">Filtering</text>
      <text x="290" y="252">+ Clip-</text><text x="290" y="265">Higher</text>
      <text x="377" y="252">+ Soft</text><text x="377" y="265">Punishment</text>
      <text x="464" y="252">+ Token-</text><text x="464" y="265">level Loss</text>
      <text x="551" y="252" font-weight="700" fill="#00805C">+ Dynamic</text><text x="551" y="265" font-weight="700" fill="#00805C">Sampling</text>
    </g>
  </g>
  <text x="355" y="288" font-size="10.5" fill="#8b949e" text-anchor="middle">Table 1 累加式消融重绘为瀑布图 · AIME 2024 avg@32 · 纵轴自 25 起（截断轴特此标注）</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">Table 1 瀑布图重绘：每叠一个机制涨一截，Dynamic Sampling 一项独占 8 分，完整 DAPO 越过 R1-Zero 参考线</figcaption>
</figure>

Dynamic Sampling 一项独占 8 分，作者解释是「熵抬起来之后，原本被牺牲的 prompt 现在能跑出有效梯度」。Token-Level Loss 只贡献 1 分，但换来训练稳定性与更健康的响应长度增长，是「分数低但不可或缺的工程保险」。

这种「把全部分数都堆到最后一项上」的累加表，比把单条消融写成「去掉这一项会掉多少分」的负向消融更能体现工程复盘的诚实：每一个机制都贡献过，缺一不可。

## 五、附录与开源交付

| 资源 | 位置 |
| --- | --- |
| 训练代码 | github.com/volcengine/verl（verl 框架本身）+ BytedTsinghua-SIA/DAPO（recipe 仓库） |
| 数据集 | DAPO-Math-17k（HuggingFace） |
| 模型权重 | DAPO-Qwen-32B（HuggingFace） |
| 项目页 | dapo-sia.github.io |
| 论文 | arXiv:2503.14476 |

文章把工程参数全部放在附录 A：训练硬件（H800 集群 × rollouts 8 卡 / actor 8 卡）、reward 设计（rule-based 正确性 + 长度惩罚）、prompt 模板、checkpoint 频率。这种「正文说服、附录兑现」的边界设计，与 Search-R1 是同一个写作传统。

## 六、能学走的三个写作技巧

1. **用「失败模式清单」组织方法节**：作者在 Introduction 就先列四个具体故障（熵坍缩、奖励噪声、训练不稳定、长度失控），第 3 节每个机制恰好对应一个故障。这比「我们设计了四个改进」更能让读者建立「机制必要性强」的直觉
2. **累加式消融比替换式消融更有力**：替换式消融（去掉 X 掉几分）只能证伪，累加式消融（叠上 X 得几分）能同时证伪与证实。Table 1 的设计是工程复盘类论文的天花板
3. **「非对称裁剪方向性」的二阶解释**：作者不只给 `ε_high > ε_low` 的数值，还给出「为何不放大下界」的二阶理由。读者拿走这套设计不需要再重新做一次反直觉的事后归因

## 尾注：对我自己工作的映射

做 OKC-SFT 的 LoRA 微调时，我们也会遇到类似「所有样本都对」或「所有样本都错」的退化批次。工业数据里同一类故障模式在 Qwen2.5-32B 的 RL 训练里被命名为「entropy collapse」，在 OKC-SFT 858 条 QA 里被命名为「同质 batch」。机制不同，名字不同，但「样本空间坍缩 → 梯度噪声放大」这个因果链是一致的。读 DAPO 的一个意外收获是：把别处的工程经验映射到自己的工作上，比直接搬公式更值。

## 参考

- 论文：arXiv:2503.14476 v2（2025-05-20），作者 Qiying Yu et al.
- 代码：github.com/volcengine/verl；recipe 仓库 github.com/BytedTsinghua-SIA/DAPO
- 数据集：huggingface.co/datasets/BytedTsinghua-SIA/DAPO-Math-17k
- 模型权重：huggingface.co/BytedTsinghua-SIA/DAPO-Qwen-32B
- 项目页：dapo-sia.github.io
- 主实验口径：AIME 2024 评估时每个问题采样 32 次报告 avg@32，推理 temperature = 1.0，top-p = 0.7
- 对照阅读：SAO（arXiv:2607.07508，GRPO 组式采样在异步场景的结构性失效与修复），本站拆解见「SAO 拆解：当 GRPO 的组式采样撞上异步 Agent 训练，160 步崩溃之后怎么救」