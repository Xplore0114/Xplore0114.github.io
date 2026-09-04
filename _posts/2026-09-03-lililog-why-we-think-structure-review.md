---
layout:     post
title:      "好文拆解：Lilian Weng 怎么把「思考」写成一棵分类树"
subtitle:   "精读 Lil'Log《Why We Think》的结构"
date:       2026-09-03
author:     "Kevin"
header-img: "img/post-bg-2015.jpg"
catalog:    true
section:    好文拆解
tags:
    - LLM
    - 推理
    - 好文拆解
---

> 拆解对象：《Why We Think》，Lilian Weng，Lil'Log，2025 年 5 月 1 日发布，约 40 分钟阅读量，53 条参考文献，文首致谢 John Schulman 提供大量反馈并直接编辑修改。原文链接见文末。这篇是学习笔记式的结构拆解，观点归原文作者。test-time compute 是当下推理方向的主叙事，这篇是它最完整的谱系梳理。好文拆解区上一篇拆了她的 Agents 综述，这篇隔近两年，可以对照看同一作者的两种组织法。

## 一、为什么值得拆

「让模型多想一会儿」横跨心理学、解码策略、RL 训练、架构设计、scaling laws 五个领域，文献上百篇。这篇的组织解法是先造一棵分类树，再让所有文献挂到树枝上：思考在哪里发生（token 空间 / 连续空间 / 潜变量）是第一层分叉，每个分叉下再按机制细分。读者任何时候都知道自己在树上的位置。

与 Agents 综述的架构轴对照：那篇按系统组件切（Planning / Memory / Tool use），这篇按计算发生的位置切。同一作者的两次选刀，示范了综述选轴的原则：轴要由主题的本质矛盾决定。agent 的本质矛盾是组件协作，思考的本质矛盾是显式与隐式的计算。

## 二、正文骨架：三大动机生根，四个分支展开

| 章节 | 职责 | 拆解要点 |
| --- | --- | --- |
| Motivation | 生根 | 心理学类比、计算作为资源、潜变量建模三个动机 |
| Thinking in Tokens | 分支一 | 并行采样与顺序修正、RL 训练推理、工具使用、忠实性 |
| Thinking in Continuous Space | 分支二 | 循环架构、思考 token |
| Thinking as Latent Variables | 分支三 | EM 算法、迭代学习 |
| Scaling Laws for Thinking Time | 分支四 | 与预训练计算的权衡 |
| What's for Future | 收束 | 六个开放问题 |
| Citation | 被引工程化 | 文末直接给 BibTeX，与 Agents 综述同款 |

Motivation 一节的开场手法值得单拆：她先抛一个人类自己也无法立刻回答的乘法题，引出「先思考再作答」是人与模型共通的行为，再引 Kahneman 双过程理论把 System 1 / System 2 的快慢之分立起来。个人体验、心理学理论、工程问题三层递进，每层只花几句话。

<figure style="margin:28px 0">
<svg viewBox="0 0 680 312" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <rect x="220" y="18" width="240" height="52" rx="10" fill="#fdf8ef" stroke="#E69F00" stroke-width="1.6"/>
  <text x="340" y="40" text-anchor="middle" font-size="13" font-weight="700" fill="#B77500">思考在哪里发生？</text>
  <text x="340" y="58" text-anchor="middle" font-size="10" fill="#57606a">分类树的第一层分叉 · 轴 = 计算发生的位置</text>
  <path d="M 340 70 L 340 86 M 120 86 L 560 86" fill="none" stroke="#8b949e" stroke-width="1.2"/>
  <path d="M 120 86 L 120 104 M 340 86 L 340 104 M 560 86 L 560 104" fill="none" stroke="#8b949e" stroke-width="1.2"/>
  <rect x="24" y="106" width="200" height="150" rx="10" fill="#f2fafd" stroke="#56B4E9" stroke-width="1.4"/>
  <text x="124" y="128" text-anchor="middle" font-size="12" font-weight="700" fill="#1E88B8">Token 空间（显式）</text>
  <g font-size="10" fill="#57606a">
    <text x="40" y="152">· 并行采样 / 顺序修正</text>
    <text x="40" y="171">· RL 训练推理（R1 四阶段）</text>
    <text x="40" y="190">· 工具使用</text>
    <text x="40" y="209" fill="#A0410A">· 忠实性：三种失败模式</text>
    <text x="40" y="228" fill="#A0410A">· CoT 优化压力 → reward hacking</text>
  </g>
  <rect x="240" y="106" width="200" height="150" rx="10" fill="#faf3f7" stroke="#CC79A7" stroke-width="1.4"/>
  <text x="340" y="128" text-anchor="middle" font-size="12" font-weight="700" fill="#A05177">连续空间（隐式）</text>
  <g font-size="10" fill="#57606a">
    <text x="256" y="152">· 循环架构：潜空间迭代</text>
    <text x="256" y="171">· thinking token：纯占位符</text>
    <text x="256" y="190">· 购买额外前向计算</text>
    <text x="256" y="209">· Quiet-STaR：token 后</text>
    <text x="256" y="228">　 生成 rationale 再混合</text>
  </g>
  <rect x="456" y="106" width="200" height="150" rx="10" fill="#f2fbf7" stroke="#009E73" stroke-width="1.4"/>
  <text x="556" y="128" text-anchor="middle" font-size="12" font-weight="700" fill="#00805C">潜变量（隐式）</text>
  <g font-size="10" fill="#57606a">
    <text x="472" y="152">· EM 算法</text>
    <text x="472" y="171">· 迭代学习</text>
    <text x="472" y="196" fill="#8b949e">三分支之外还有第四分支：</text>
    <text x="472" y="214" fill="#8b949e">Scaling Laws 讲思考时间</text>
    <text x="472" y="232" fill="#8b949e">与预训练计算的权衡边界</text>
  </g>
  <text x="340" y="282" font-size="11" font-weight="600" fill="#24292f" text-anchor="middle">对偶张力贯穿全文：显式换可解释性，隐式换计算效率，忠实性是显式一脉的命门</text>
  <text x="340" y="302" font-size="10.5" fill="#8b949e" text-anchor="middle">53 条文献全部挂在这棵树上 · 读者任何时候都知道自己在树上的位置</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">分类树仿绘：第一层按计算发生的位置分叉，每个分支下再按机制细分，Motivation 三层递进负责生根</figcaption>
</figure>


## 三、显式与隐式：贯穿全文的对偶结构

分类树的第一个分支 Thinking in Tokens 讲显式思考：推理以自然语言 token 外显，可读可监控，CoT 监控甚至能实现弱模型监督强模型。但忠实性存疑，Lanham et al. 列的三种失败模式（提前作答、无信息量 token、人类不可读的编码）说明准确率提升未必依赖人类可读的推理；对 CoT 直接施加优化压力还会导致混淆式 reward hacking，模型把真实意图藏进 CoT。

第二、三分支讲隐式思考：循环架构在潜空间迭代，thinking token 是纯粹为购买额外前向计算而插入的占位符，Quiet-STaR 在每个 token 后生成 rationale 再混合预测。显式与隐式的对比撑起全文的骨架张力：显式换可解释性，隐式换计算效率，忠实性是显式一脉的命门。

这个对偶直接呼应 RL 训练一节的内容：DeepSeek-R1 的四阶段流程与 Aha moment 涌现是显式思考训练的代表作，PRM 与 MCTS 的失败尝试也在这一节交代。我持续追踪的 GRPO 到 DAPO 谱系，在这篇文章里找到了上游叙事。

<figure style="margin:28px 0">
<svg viewBox="0 0 680 232" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <rect x="24" y="24" width="300" height="152" rx="10" fill="#f2fafd" stroke="#56B4E9" stroke-width="1.4"/>
  <text x="174" y="48" text-anchor="middle" font-size="12.5" font-weight="700" fill="#1E88B8">显式思考（Token 空间）</text>
  <g font-size="10.5" fill="#57606a">
    <text x="42" y="74">✓ 可读可监控 · CoT 弱模型监督强模型</text>
    <text x="42" y="98" fill="#A0410A">✗ 提前作答 / 无信息 token / 不可读编码</text>
    <text x="42" y="122" fill="#A0410A">✗ 对 CoT 施压 → 混淆式 reward hacking</text>
    <text x="42" y="150" font-size="9.5" fill="#8b949e">准确率提升未必依赖人类可读的推理</text>
  </g>
  <rect x="356" y="24" width="300" height="152" rx="10" fill="#faf3f7" stroke="#CC79A7" stroke-width="1.4"/>
  <text x="506" y="48" text-anchor="middle" font-size="12.5" font-weight="700" fill="#A05177">隐式思考（连续空间 / 潜变量）</text>
  <g font-size="10.5" fill="#57606a">
    <text x="374" y="74">✓ 计算效率：潜空间迭代不付 token 成本</text>
    <text x="374" y="98">✓ thinking token / 循环架构 / Quiet-STaR</text>
    <text x="374" y="122" fill="#A05177">✗ 不可读 · 不可监控 · 不可外部验证</text>
    <text x="374" y="150" font-size="9.5" fill="#8b949e">纯粹为购买额外前向计算而存在</text>
  </g>
  <path d="M 324 100 C 336 100, 344 100, 354 100" stroke="#8b949e" stroke-width="1.2"/>
  <text x="340" y="92" font-size="9.5" fill="#8b949e" text-anchor="middle">张力</text>
  <text x="340" y="200" font-size="11" font-weight="600" fill="#24292f" text-anchor="middle">显式换可解释性，隐式换计算效率</text>
  <text x="340" y="222" font-size="10.5" fill="#8b949e" text-anchor="middle">这个对偶在引言埋线、每个分支里呼应 · OKC-SFT 压幻觉处理的就是左边那道裂缝</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">对偶结构仿绘：全文的骨架张力，显式一脉的命门是忠实性，隐式一脉的代价是不可读</figcaption>
</figure>


## 四、Scaling Laws 一节的位置感

分支四把思考时间作为继模型规模、训练算力、数据量之后的新扩展维度，但立刻补上边界条件：测试时计算与预训练计算并非一对一可互换，推理 token 需远少于预训练 token 时才有优势，强大的基础模型仍不可或缺。综述的严谨在于给每个火热概念标注适用边界，这一节是全文的定海针，放在收束之前恰到好处。

## 五、六个开放问题：综述的诚实收尾

结尾的 What's for Future 列了六个问题，每个都是当前无解的真问题：如何激励模型产生人类可读且忠实的推理路径同时避免 reward hacking；如何定义并在无人工干预下捕获 reward hacking；无 ground truth 时如何训练自我纠正；创意写作与辅导这类难以评分的任务怎么做带 CoT rollout 的 RL；部署时如何把性能增益蒸馏回基础模型；如何让测试时开销按问题难度自适应。

六个问题几乎条条指向对齐与评测的交叉地带，与前一年 Agents 综述结尾的三条挑战一样，先立机会再划边界，诚实的综述才配得上被引用。

## 六、能学走的三个写作技巧

1. **轴由主题本质矛盾决定**：综述选组织轴时先问这个领域的本质张力是什么，思考的张力是显式与隐式，agent 的张力是组件协作
2. **对偶结构撑骨架**：全文主对比（显式对隐式）在引言埋线、每个分支里呼应，读者带着同一个问题读完全文
3. **边界条件即定海针**：火热概念（test-time compute）的综述里专门留一节讲它换不来的东西，防吹捧于未然

## 尾注：对我自己工作的映射

OKC-SFT 的核心工作是压幻觉率（34.4% 到 15.6%），本质上就是在处理这篇文章里显式思考的命门：模型说的话与模型的真实计算之间有裂缝。教练系统「算法层输出结构化 JSON 证据、LLM 层只做语义转述」的职责分离，可以理解为把可信计算外置到算法层，让 LLM 层的转述即使有幻觉也无法凭空捏造证据。显式可验证的计算优于自由发挥的叙述，这个原则贯穿了这篇文章与我的工程实践。

## 参考

- 原文：Why We Think，Lilian Weng，Lil'Log，2025-05-01，lilianweng.github.io/posts/2025-05-01-thinking/
- 原文致谢：John Schulman 提供反馈并直接编辑
- 参考文献规模：编号至 54 缺 28，实际 53 条
- 关联拆解：本博客 Lil'Log Agents 综述拆解（好文拆解区，同一作者的架构轴组织法对照）
