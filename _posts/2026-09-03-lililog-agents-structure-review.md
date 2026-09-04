---
layout:     post
title:      "好文拆解：Lilian Weng 怎么用一张架构图写活 agent 综述"
subtitle:   "精读 Lil'Log《LLM Powered Autonomous Agents》的结构"
date:       2026-09-03
author:     "Kevin"
header-img: "img/post-bg-2015.jpg"
catalog:    true
section:    好文拆解
tags:
    - LLM
    - 智能体
    - 好文拆解
---

> 拆解对象：《LLM Powered Autonomous Agents》，Lilian Weng（时任 OpenAI 安全系统负责人，后任研究与安全副总裁），发表于个人博客 Lil'Log，2023 年 6 月 23 日，约 31 分钟阅读量，21 条参考文献。原文链接见文末。这篇是学习笔记式的结构拆解，观点归原文作者。它是 agent 方向被引用最多的综述长文，本系列之前拆过的 ReAct、Reflexion、ToT 全部被它收编进同一张架构图，读完这篇拆解再回去看那三篇，谱系会立刻清晰。

## 一、为什么值得拆

综述式长文有个组织难题：按文献时间线写会变成流水账，按主题写又容易碎片化。这篇文章给出了第三种答案：按系统架构切。全文只有一条主线，即 LLM 是大脑，大脑之外挂三个组件，Planning 负责拆任务，Memory 负责存取经验，Tool use 负责伸出体外。所有文献都挂在这条线上，读者随时知道自己在哪里。

这个切法后来成了行业通用词汇。工程圈讨论 agent 时说的规划、记忆、工具三件套，源头就是这篇文章的三个章节标题。一篇文章定义了一个领域的讨论框架，这就是结构的力量。

## 二、正文骨架：一张图定死目录

| 章节 | 职责 | 拆解要点 |
| --- | --- | --- |
| Agent System Overview | 立论兼目录 | 一张总览图：LLM 居中，Planning / Memory / Tool use 三组件环绕 |
| Component One: Planning | 组件一 | 任务分解、自我反思两个子节，方法谱系逐一进场 |
| Component Two: Memory | 组件二 | 人脑记忆类比映射，落到 MIPS 检索算法 |
| Component Three: Tool Use | 组件三 | MRKL 到 HuggingGPT 的工具调用进化线 |
| Case Studies | 落地证据 | 严肃科研、学术模拟、概念验证三档 |
| Challenges | 诚实的收尾 | 三条硬伤全部直说 |

开篇的总览图就是全文目录的图形化：图里三个组件框，正文三个 Component 章节，一一对应。读者看完图就能预测全文结构，预测成真是好结构的基本特征。

<figure style="margin:28px 0">
<svg viewBox="0 0 680 344" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs><marker id="ll-a" markerWidth="6" markerHeight="6" refX="4.5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#57606a"/></marker></defs>
  <rect x="270" y="126" width="140" height="66" rx="12" fill="#fdf8ef" stroke="#E69F00" stroke-width="1.8"/>
  <text x="340" y="154" text-anchor="middle" font-size="14" font-weight="700" fill="#B77500">LLM</text>
  <text x="340" y="174" text-anchor="middle" font-size="10.5" fill="#57606a">大脑 · 中枢控制器</text>
  <rect x="24" y="30" width="220" height="176" rx="10" fill="#f2fafd" stroke="#56B4E9" stroke-width="1.4"/>
  <text x="134" y="52" text-anchor="middle" font-size="12.5" font-weight="700" fill="#1E88B8">Planning · 拆任务</text>
  <g font-size="10" fill="#57606a">
    <text x="40" y="76" font-weight="600">任务分解（复杂度递进）</text>
    <text x="52" y="93">CoT → ToT（BFS/DFS）→ LLM+P（PDDL）</text>
    <text x="40" y="119" font-weight="600">自我反思（手段递进）</text>
    <text x="52" y="136">ReAct → Reflexion → CoH → Algo Distill</text>
    <text x="40" y="162" font-size="9.5" fill="#8b949e">排序藏在工程品味里：最便宜的方案先列</text>
    <text x="40" y="180" font-size="9.5" fill="#8b949e">Challenges 对应：长程规划遇错难调整</text>
  </g>
  <rect x="436" y="30" width="220" height="176" rx="10" fill="#faf3f7" stroke="#CC79A7" stroke-width="1.4"/>
  <text x="546" y="52" text-anchor="middle" font-size="12.5" font-weight="700" fill="#A05177">Memory · 存经验</text>
  <g font-size="10" fill="#57606a">
    <text x="452" y="76" font-weight="600">人脑记忆类比映射</text>
    <text x="464" y="93">感觉 → embedding 输入</text>
    <text x="464" y="110">短期 → 上下文窗口（约 7 项）</text>
    <text x="464" y="127">长期 → 外部向量库</text>
    <text x="452" y="153" font-weight="600">检索 = MIPS</text>
    <text x="464" y="170">LSH · ANNOY · HNSW · FAISS · ScaNN</text>
    <text x="452" y="190" font-size="9.5" fill="#8b949e">Challenges 对应：表达力不如 full attention</text>
  </g>
  <path d="M 244 110 C 258 110, 260 140, 268 148" fill="none" stroke="#57606a" stroke-width="1.3" marker-end="url(#ll-a)"/>
  <path d="M 436 110 C 422 110, 420 140, 412 148" fill="none" stroke="#57606a" stroke-width="1.3" marker-end="url(#ll-a)"/>
  <path d="M 340 192 L 340 212" fill="none" stroke="#57606a" stroke-width="1.3" marker-end="url(#ll-a)"/>
  <rect x="24" y="216" width="632" height="72" rx="10" fill="#f2fbf7" stroke="#009E73" stroke-width="1.4"/>
  <text x="46" y="242" font-size="12.5" font-weight="700" fill="#00805C">Tool use · 伸出体外</text>
  <text x="46" y="264" font-size="10" fill="#57606a">进化线：MRKL → HuggingGPT · 案例：ChemCrow（13 个专家工具，ReAct 格式）· AutoGPT（正文直接贴 system message）</text>
  <text x="46" y="280" font-size="9.5" fill="#8b949e">Challenges 对应：自然语言接口可靠性存疑，demo 代码精力耗在解析模型输出上</text>
  <text x="340" y="316" font-size="10.5" fill="#8b949e" text-anchor="middle">Figure 1 总览图仿绘 · 三个组件框 = 正文三个 Component 章节 · 结尾三条 Challenges 与三组件一一对应</text>
  <text x="340" y="336" font-size="10.5" fill="#8b949e" text-anchor="middle">本系列已拆的 ReAct、Reflexion 都挂在这张图的 Planning 分支上</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">总览图仿绘：一张图定死目录，LLM 是大脑、三个组件环绕，读者看完图就能预测全文结构</figcaption>
</figure>


## 三、Planning 章：方法谱系的进场顺序有讲究

任务分解子节里，方法按复杂度递增进场：CoT（链式思考）到 ToT（树状搜索，每步多分支，用 BFS 或 DFS 配合分类器评估）到 LLM+P（干脆把规划外包给外部经典规划器，用 PDDL 做中间语言）。一条从提示工程到符号系统的光谱，读者顺着走就能理解每一步的增量。

自我反思子节同样有递进：ReAct 把推理和行动交错（Thought / Action / Observation 模板），Reflexion 给 agent 加动态记忆与自我反思，CoH 把带反馈标注的历史输出喂给模型训练，Algorithm Distillation 再把同样的思想搬到 RL 的跨 episode 轨迹上。从提示、到记忆、到微调、到 RL，四种实现反思的手段排成一列。

值得学的细节是任务分解的开场：她给了三种分解方式，第一种就是一句简单提示（"Steps for XYZ. 1."），第二种任务特定指令，第三种人工输入。从最便宜的方案开始列举，工程品味藏在排序里。

## 四、Memory 章：类比是组织知识的杠杆

这章的核心是一张映射表：

| 人脑记忆 | agent 系统对应 |
| --- | --- |
| 感觉记忆 | 原始输入的 embedding 表示 |
| 短期记忆（约 7 项，持续 20-30 秒，Miller 1956） | 上下文学习，受 Transformer 有限上下文窗口约束 |
| 长期记忆 | 外部向量存储，按需快速检索 |

一个认知心理学的经典框架直接平移到工程系统，读者不需要新学任何概念就能记住三组件里的记忆设计。落到实现层，她把长期记忆的检索问题命名为 MIPS（最大内积搜索），列举 LSH、ANNOY、HNSW、FAISS、ScaNN 五个算法。类比负责让人懂，算法名负责让人能动手，两层衔接顺畅。

<figure style="margin:28px 0">
<svg viewBox="0 0 680 216" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs><marker id="lm-a" markerWidth="6" markerHeight="6" refX="4.5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#57606a"/></marker></defs>
  <text x="170" y="28" text-anchor="middle" font-size="12" font-weight="700" fill="#57606a">人脑记忆（Miller 1956）</text>
  <text x="500" y="28" text-anchor="middle" font-size="12" font-weight="700" fill="#A05177">agent 系统对应</text>
  <g font-size="11">
    <rect x="40" y="44" width="260" height="40" rx="8" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="56" y="62">感觉记忆</text><text x="56" y="78" font-size="9.5" fill="#8b949e">毫秒级原始输入缓冲</text>
    <rect x="380" y="44" width="260" height="40" rx="8" fill="#faf3f7" stroke="#CC79A7" stroke-opacity=".6"/>
    <text x="396" y="62">原始输入的 embedding 表示</text><text x="396" y="78" font-size="9.5" fill="#8b949e">进模型前的向量化形态</text>
    <line x1="300" y1="64" x2="378" y2="64" stroke="#57606a" stroke-width="1.2" marker-end="url(#lm-a)"/>
    <rect x="40" y="94" width="260" height="40" rx="8" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="56" y="112">短期记忆</text><text x="56" y="128" font-size="9.5" fill="#8b949e">约 7 项 · 持续 20-30 秒</text>
    <rect x="380" y="94" width="260" height="40" rx="8" fill="#faf3f7" stroke="#CC79A7" stroke-opacity=".6"/>
    <text x="396" y="112">上下文学习</text><text x="396" y="128" font-size="9.5" fill="#8b949e">受 Transformer 上下文窗口约束</text>
    <line x1="300" y1="114" x2="378" y2="114" stroke="#57606a" stroke-width="1.2" marker-end="url(#lm-a)"/>
    <rect x="40" y="144" width="260" height="40" rx="8" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="56" y="162">长期记忆</text><text x="56" y="178" font-size="9.5" fill="#8b949e">容量近乎无限 · 按需提取</text>
    <rect x="380" y="144" width="260" height="40" rx="8" fill="#faf3f7" stroke="#CC79A7" stroke-opacity=".6"/>
    <text x="396" y="162">外部向量存储 + MIPS 检索</text><text x="396" y="178" font-size="9.5" fill="#8b949e">LSH · ANNOY · HNSW · FAISS · ScaNN</text>
    <line x1="300" y1="164" x2="378" y2="164" stroke="#57606a" stroke-width="1.2" marker-end="url(#lm-a)"/>
  </g>
  <text x="340" y="208" font-size="10.5" fill="#8b949e" text-anchor="middle">类比负责让人懂，算法名负责让人能动手：记忆章的两层衔接</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">记忆映射仿绘：认知心理学框架平移到工程系统，长期记忆的检索被命名为 MIPS 并给出五个可用算法</figcaption>
</figure>


## 五、Case Studies 章：三档案例的层次感

| 档位 | 案例 | 作用 |
| --- | --- | --- |
| 严肃科研 | ChemCrow（13 个专家工具覆盖有机合成与药物发现，LangChain 实现，遵循 ReAct 格式）；Boiko et al. 自主科学实验 agent | 证明架构在真实科研场景成立 |
| 学术模拟 | Generative Agents（25 个 LLM 驱动角色在沙盒小镇生活，记忆流按相关性、新近性、重要性检索） | 证明记忆组件的学术深度 |
| 概念验证 | AutoGPT、GPT-Engineer（直接贴出完整 system message） | 给读者可复现的入口 |

第三档直接贴 system message 是个亮点：综述长文通常止步于引用，她把 AutoGPT 的完整提示词放进正文，读者复制就能跑。可复现性从口号变成复制粘贴的成本。

Boiko et al. 案例里她还原文披露了安全性数据：11 条被判定为高危的请求中有 4 条得到了合成方案。综述不回避自己引用工作的安全瑕疵，这种诚实与结尾的 Challenges 章呼应。

## 六、Challenges 章：诚实是综述的可信度来源

结尾三条挑战全部直说硬伤，且每条都带延伸判断：有限上下文长度限制了历史信息、指令与 API 调用上下文的容纳，向量检索虽然扩大了知识池，但其表达能力不如 full attention；长期规划与任务分解仍然困难，LLM 遇到意外错误时难以调整计划，健壮性不如人类从试错中学习；自然语言接口的可靠性存疑，格式错误与拒绝执行时有发生，大量 agent demo 代码的精力都耗在解析模型输出上。

三条挑战分别对应前文三个组件的局限，结构与首尾闭环。写综述把被综述方向的边界讲清楚，读者才会信任你讲的机会。

## 七、能学走的三个写作技巧

1. **架构轴替代文献轴**：组织综述时先画系统图，再让文献各就各位，避免流水账
2. **类比降认知门槛**：用人脑记忆这类成熟框架映射工程概念，读者零新概念入门
3. **文末直接给 BibTeX**：她把 Citation 写成固定格式并附 BibTeX，把被引用这件事工程化，这篇文章后来被引用数万次，格式化引用降低了引用成本

## 尾注：对我自己工作的映射

赛后教练系统的六环节 pipeline 可以直接对上这张架构图：轨迹理解到行为诊断对应 Planning 的任务分解，漂移技巧分类表就是结构化的长期记忆，改善验证环节依赖的自动判据正是 Challenges 第三条说的可靠接口问题。算法层坚持输出结构化 JSON、LLM 层只做语义转述，本质上就是在回应「自然语言接口可靠性存疑」这条挑战。

## 参考

- 原文：LLM Powered Autonomous Agents，Lilian Weng，Lil'Log，2023-06-23，lilianweng.github.io/posts/2023-06-23-agent/
- 原文引用计数：21 条参考文献，含 17 篇论文、2 个 GitHub 项目（AutoGPT、GPT-Engineer）、2 篇博客、1 条 ChatGPT 对话链接
- 关联拆解：本博客 ReAct 拆解（Planning 章的反思谱系起点）、Reflexion 拆解（反思谱系第二站）、WebRL 拆解（Tool use 与评测的后续演化）
