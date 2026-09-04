---
layout:     post
title:      "Search-R1 拆解：COLM 2025 论文怎么把「RL + 搜索引擎」讲清楚"
subtitle:   "从结构解剖视角读一篇 agentic RL 范式之作"
date:       2026-09-03
author:     "Kevin"
header-img: "img/post-bg-2015.jpg"
catalog:    true
section:    论文拆解
tags:
    - LLM
    - 强化学习
    - 论文拆解
---

> 拆解对象：Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning，COLM 2025。作者来自 UIUC、UMass Amherst 与 Google Cloud AI Research，一作 Bowen Jin，开源代码在 GitHub 收获 5k+ star。这篇文章只做一件事：分析这篇论文的结构为什么好。所有数字出自论文 arXiv 最新版的正文与附录，可对照原表复核。

## 一、为什么值得拆

在「R1 系列方法 + 工具调用」这个方向上，Search-R1 是被后续工作引用最多的范式之作之一。它回答的问题很朴素：让模型在推理过程中自主决定什么时候搜索、搜什么、怎么用搜索结果，能不能纯靠强化学习学会，完全绕开检索增强生成（RAG）的固定流程，也绕开工具调用的监督微调数据依赖。

这个「朴素问题 + 干净答案」的组合，恰好让它成为方法论文写作的拆解样本。

## 二、正文三幕：方法论文的标准骨架

| 章节 | 职责 | 拆解要点 |
| --- | --- | --- |
| 1 Introduction | 立论 | 点名旧路线的两个具体缺陷：RAG 检索流程固定，工具调用 SFT 依赖大规模标注 |
| 2 Related Works | 双线定位 | 2.1 LLM 与检索、2.2 LLM 与强化学习，两条线各自铺到本文位置 |
| 3 Search-R1 | 方法主体 | 四个子节按依赖顺序排布（下节展开） |
| 4 Main Results | 主实验 | 7 个 QA 数据集 × 8 个基线，EM 指标一张主表收拢 |
| 5 Analysis | 分析 | 四个彼此独立的问题，任何一问都单独成立 |
| 6 Conclusions | 收束 | 一页以内 |

正文只有 6 节，公式推导、超参数、案例研究全部下沉到附录 A 到 J。方法论文的核心资产是方法与主结果，验证性内容一律后置，这个取舍在章节比例上体现得非常自觉。

## 三、方法节的排布：每个子节解决一个「让 RL 跑通」的必要条件

第 3 节的四个子节值得逐个看：

| 子节 | 内容 | 解决的必要条件 |
| --- | --- | --- |
| 3.1 RL with a Search Engine | 统一形式化，内含 Loss Masking for Retrieved Tokens，以及 PPO 与 GRPO 两个变体 | 训练目标成立：检索 token 不进策略梯度 |
| 3.2 Multi-turn Calling | 多轮搜索交互的 rollout 伪代码（Algorithm 1） | 交互流程成立：一次 rollout 允许多次搜索 |
| 3.3 Training Template | think / search / information / answer 四标签模板 | 接口成立：模型怎么「说出」一次搜索 |
| 3.4 Reward Modeling | 纯 outcome 的规则式 EM 奖励 | 信号成立：答对给 1，答错给 0，无格式奖励 |

<figure style="margin:28px 0">
<svg viewBox="0 0 680 330" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="sr-a" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#57606a"/></marker>
    <pattern id="sr-mask" width="8" height="8" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#f6f8fa"/><line x1="0" y1="0" x2="0" y2="8" stroke="#c9d1d9" stroke-width="3"/></pattern>
  </defs>
  <rect x="30" y="22" width="230" height="42" rx="8" fill="#fff" stroke="#d0d7de"/>
  <text x="145" y="47" text-anchor="middle" font-size="12" fill="#24292f">问题：谁发明了回旋加速器？</text>
  <line x1="145" y1="64" x2="145" y2="82" stroke="#57606a" stroke-width="1.3" marker-end="url(#sr-a)"/>
  <rect x="30" y="86" width="400" height="204" rx="10" fill="#fff" stroke="#d0d7de" stroke-width="1.4"/>
  <text x="230" y="108" text-anchor="middle" font-size="12.5" font-weight="700" fill="#24292f">LLM（策略 πθ）· 四标签模板</text>
  <g font-size="11" text-anchor="middle">
    <rect x="52" y="120" width="356" height="24" rx="6" fill="#eafaf4" stroke="#009E73"/><text x="230" y="136" fill="#005C42" font-weight="600">&lt;think&gt; 需要确认发明者身份，先搜索 &lt;/think&gt;</text>
    <line x1="230" y1="144" x2="230" y2="155" stroke="#57606a" stroke-width="1.2" marker-end="url(#sr-a)"/>
    <rect x="52" y="157" width="356" height="24" rx="6" fill="#f2fafd" stroke="#56B4E9"/><text x="230" y="173" fill="#1E88B8" font-weight="600">&lt;search&gt; cyclotron inventor &lt;/search&gt;</text>
    <line x1="230" y1="181" x2="230" y2="192" stroke="#57606a" stroke-width="1.2" marker-end="url(#sr-a)"/>
    <rect x="52" y="194" width="356" height="24" rx="6" fill="url(#sr-mask)" stroke="#8b949e" stroke-dasharray="5 3"/><text x="230" y="210" fill="#57606a">&lt;information&gt; Lawrence, 1930 … &lt;/information&gt;</text>
    <line x1="230" y1="218" x2="230" y2="229" stroke="#57606a" stroke-width="1.2" marker-end="url(#sr-a)"/>
    <rect x="52" y="231" width="356" height="24" rx="6" fill="#eafaf4" stroke="#009E73"/><text x="230" y="247" fill="#005C42" font-weight="600">&lt;think&gt; 证据指向 Ernest Lawrence &lt;/think&gt;</text>
    <line x1="230" y1="255" x2="230" y2="263" stroke="#57606a" stroke-width="1.2" marker-end="url(#sr-a)"/>
    <rect x="52" y="264" width="356" height="20" rx="6" fill="#fff" stroke="#009E73" stroke-width="1.6"/><text x="230" y="278" fill="#24292f" font-weight="600">&lt;answer&gt; Ernest O. Lawrence &lt;/answer&gt;</text>
  </g>
  <rect x="470" y="150" width="180" height="88" rx="10" fill="#fdf8ef" stroke="#E69F00" stroke-width="1.4"/>
  <text x="560" y="178" text-anchor="middle" font-size="12.5" font-weight="700" fill="#B77500">搜索引擎</text>
  <text x="560" y="198" text-anchor="middle" font-size="10.5" fill="#57606a">E5 检索 · Wikipedia</text>
  <text x="560" y="214" text-anchor="middle" font-size="10.5" fill="#57606a">top-3 · 最多 4 次调用</text>
  <path d="M 448 169 L 470 169" stroke="#56B4E9" stroke-width="1.6" marker-end="url(#sr-a)" fill="none"/>
  <text x="458" y="160" font-size="9.5" fill="#1E88B8" text-anchor="middle">查询</text>
  <path d="M 470 223 C 460 223, 455 206, 448 206" stroke="#8b949e" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#sr-a)" fill="none"/>
  <text x="456" y="240" font-size="9.5" fill="#8b949e" text-anchor="middle">返回</text>
  <text x="340" y="316" text-anchor="middle" font-size="10.5" fill="#8b949e">斜纹段是检索 token：进上下文、进奖励计算，但被 loss masking 排除出策略梯度（机制 3.1 提出，5.4 节消融验证）</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">四标签模板与 loss masking 仿绘：模型生成的 think / search / answer 进策略梯度，环境注入的 information 被遮罩</figcaption>
</figure>

这个顺序是依赖序。最大的工程风险（检索 token 混入策略梯度导致训练不稳）在第一个子节就用 loss masking 处理掉，读者按顺序读完，恰好具备复现的全部要素。

loss masking 的「提出与验证」跨节闭环也很讲究：机制在 3.1 提出，效果在 5.4 节与 Table 4 验证，Qwen2.5-7B 有 mask 平均 EM 0.431 对无 mask 0.343，3B 上为 0.303 对 0.262，完整研究再放附录 D。一个机制从动机、设计到消融形成完整证据链。

## 四、分析节是第二个贡献区

第 5 节的四问，每一问都踩在社区关心的开放问题上：

1. **PPO 还是 GRPO**（5.1）：GRPO 收敛更快，PPO 依赖 critic 预热起步慢；但 GRPO 长时间训练会出现奖励崩溃，PPO 全程稳定，论文因此默认 PPO。典型数据：7B base 模型 PPO 平均 0.431 对 GRPO 0.350，3B 上 GRPO 0.312 略高于 PPO 0.303，印证最终性能相当。DeepSeek-R1 引爆 GRPO 之后，这张对比表直接回应了当时最热的争议
2. **Base 还是 Instruct**（5.2）：base 模型是更好的训练起点
3. **响应长度与有效搜索动态**（5.3）：训练中响应长度先降后升再稳定，有效搜索次数持续增加
4. **loss masking 消融**（5.4）：见上节

方法论文的主表证明「有效」，分析节证明「可迁移」。Table 3 的 PPO/GRPO 对比在正文之外额外贡献了一组别人可以直接引用的实证结论，这是分析节的天花板。

<figure style="margin:28px 0">
<svg viewBox="0 0 680 262" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <g stroke="#eaeef2"><line x1="60" y1="205" x2="620" y2="205"/><line x1="60" y1="165" x2="620" y2="165"/><line x1="60" y1="125" x2="620" y2="125"/><line x1="60" y1="85" x2="620" y2="85"/><line x1="60" y1="45" x2="620" y2="45"/></g>
  <g font-size="10.5" fill="#8b949e"><text x="54" y="209" text-anchor="end">0.20</text><text x="54" y="169" text-anchor="end">0.30</text><text x="54" y="129" text-anchor="end">0.40</text><text x="54" y="89" text-anchor="end">0.50</text><text x="54" y="49" text-anchor="end">0.60</text></g>
  <line x1="60" y1="210" x2="620" y2="210" stroke="#d0d7de"/>
  <g font-size="11" text-anchor="middle" fill="#57606a">
    <rect x="120" y="20" width="60" height="13" rx="2" fill="#009E73"/><text x="190" y="30">有 mask</text>
    <rect x="260" y="20" width="60" height="13" rx="2" fill="#E69F00"/><text x="330" y="30">无 mask</text>
    <rect x="410" y="20" width="60" height="13" rx="2" fill="#56B4E9"/><text x="480" y="30">PPO</text>
    <rect x="545" y="20" width="60" height="13" rx="2" fill="#CC79A7"/><text x="615" y="30">GRPO</text>
  </g>
  <g>
    <rect x="90" y="90" width="90" height="115" rx="6" fill="#009E73"/>
    <rect x="230" y="133" width="90" height="72" rx="6" fill="#E69F00"/>
    <rect x="390" y="90" width="90" height="115" rx="6" fill="#56B4E9"/>
    <rect x="525" y="152" width="90" height="53" rx="6" fill="#CC79A7"/>
    <g font-size="12.5" font-weight="700" fill="#24292f" text-anchor="middle">
      <text x="135" y="82">0.431</text><text x="275" y="125">0.343</text><text x="435" y="82">0.431</text><text x="570" y="144">0.350</text>
    </g>
    <g font-size="12" font-weight="700" fill="#24292f" text-anchor="middle">
      <text x="215" y="232">Qwen2.5-7B base</text><text x="500" y="232">Qwen2.5-7B base</text>
    </g>
    <text x="215" y="250" font-size="10.5" fill="#8b949e" text-anchor="middle">loss masking 消融（Table 4）</text>
    <text x="500" y="250" font-size="10.5" fill="#8b949e" text-anchor="middle">PPO vs GRPO（Table 3）</text>
  </g>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">两组关键数字重绘：左为 loss masking 消融（7B 平均 EM 0.431 对 0.343），右为算法对比（7B 上 PPO 0.431 对 GRPO 0.350）</figcaption>
</figure>


## 五、附录 A 到 J：把可复现做成结构

| 附录 | 内容 |
| --- | --- |
| A | RL 形式化的完整公式推导 |
| B | 实验设置与全部超参数（8×H100，检索器 E5，2018 年 Wikipedia 语料，默认 top-3，最多 4 次搜索调用） |
| C | 14B 模型主结果（平均 EM 进一步到 0.479） |
| D / E / F | loss masking、base vs instruct、PPO vs GRPO 的完整研究 |
| G | 检索 top-k 研究（top-3 最优，0.431） |
| H | GRPO group size 研究（size=1 泛化最好，0.410） |
| I / J | R1 与 Search-R1 的案例对比、更多成功失败案例 |

正文管说服，附录管复现，边界干净。开源仓库加数据集 checkpoint 齐全，结构上的「可复现承诺」由附录与代码共同兑现。

## 六、能学走的三个写作技巧

1. **一张图讲两种算法路径**：Figure 1 同时画出 PPO 与 GRPO 的 rollout 结构，读者第一次见到框架就建立「本方法与具体 RL 算法无关」的认知，5.1 节的对比因此不突兀
2. **奖励极简主义**：纯 EM 规则奖励，没有格式奖励，没有过程奖励，把「方法的有效性」与「奖励工程的复杂性」彻底解耦，结论反而更可信
3. **训练动态图当证据**：Figure 2 四联图（算法对比、base/instruct、长度变化、搜索次数）用同一组训练曲线支撑四个分析结论，比只报终态分数更有说服力

## 尾注：对我自己工作的映射

做 QQ 飞车赛后教练系统时，我们定了「算法层输出结构化证据、LLM 层只做语义转述」的职责分离。Search-R1 的 loss masking 是同一思想在训练侧的版本：检索 token 属于环境，策略梯度只作用于模型自己生成的 token。环境的信息可以进上下文，但更新权重的责任必须分清。凡是「模型生成」与「外部注入」混在一条序列里的训练场景，这个masking 设计都值得先想一遍。

## 参考

- 论文：arXiv:2503.09516，发表于 COLM 2025（The 2nd Conference on Language Modeling）
- 代码：github.com/PeterGriffinJin/Search-R1
- 主实验口径：7 个数据集为 NQ、TriviaQA、PopQA、HotpotQA、2WikiMultiHopQA、Musique、Bamboogle，其中 NQ 与 HotpotQA 为域内，其余五个域外，指标为 Exact Match
