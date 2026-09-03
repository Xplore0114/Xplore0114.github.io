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

这个顺序是依赖序。最大的工程风险（检索 token 混入策略梯度导致训练不稳）在第一个子节就用 loss masking 处理掉，读者按顺序读完，恰好具备复现的全部要素。

loss masking 的「提出与验证」跨节闭环也很讲究：机制在 3.1 提出，效果在 5.4 节与 Table 4 验证，Qwen2.5-7B 有 mask 平均 EM 0.431 对无 mask 0.343，3B 上为 0.303 对 0.262，完整研究再放附录 D。一个机制从动机、设计到消融形成完整证据链。

## 四、分析节是第二个贡献区

第 5 节的四问，每一问都踩在社区关心的开放问题上：

1. **PPO 还是 GRPO**（5.1）：GRPO 收敛更快，PPO 依赖 critic 预热起步慢；但 GRPO 长时间训练会出现奖励崩溃，PPO 全程稳定，论文因此默认 PPO。典型数据：7B base 模型 PPO 平均 0.431 对 GRPO 0.350，3B 上 GRPO 0.312 略高于 PPO 0.303，印证最终性能相当。DeepSeek-R1 引爆 GRPO 之后，这张对比表直接回应了当时最热的争议
2. **Base 还是 Instruct**（5.2）：base 模型是更好的训练起点
3. **响应长度与有效搜索动态**（5.3）：训练中响应长度先降后升再稳定，有效搜索次数持续增加
4. **loss masking 消融**（5.4）：见上节

方法论文的主表证明「有效」，分析节证明「可迁移」。Table 3 的 PPO/GRPO 对比在正文之外额外贡献了一组别人可以直接引用的实证结论，这是分析节的天花板。

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
