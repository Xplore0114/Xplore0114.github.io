---
layout:     post
title:      "好文拆解：Anthropic 怎么把 agent 工程写成设计模式手册"
subtitle:   "精读《Building Effective Agents》的结构"
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

> 拆解对象：《Building Effective Agents》，Erik Schluntz 与 Barry Zhang 执笔，Anthropic Engineering Blog，2024 年 12 月 19 日发布。原文链接见文末。这篇是学习笔记式的结构拆解，观点归原文作者。这是工程博客里被引用最多的 agent 方法论文章，全篇没有一个新实验、没有一张 benchmark 表，说服力全部来自结构。对比本系列的论文拆解（都在卖数据），这篇恰好示范了没有数据的方法论文章怎么立住。

## 一、为什么值得拆

大部分工程博客的宿命是发完即沉，这篇文章却成了 agent 工程的引用锚点：workflows 与 agents 的二分法、五种工作流模式的名字、ACI 的提法，后来到处都在用。它做对的事有三件：先定义再分用、模式命名化、把劝退放在教学前面。三者全是结构决策，与方法本身的新颖度无关。

开篇一句话就是立场：与数十个行业团队合作下来，最成功的实现用的都是简单、可组合的模式，而非复杂框架。全文所有章节都在为这句话服务。

## 二、正文骨架：复杂度递增的目录即叙事

| 章节 | 职责 | 拆解要点 |
| --- | --- | --- |
| What are agents? | 定义先行 | agentic systems 为总称，workflows 与 agents 二分 |
| When (and when not) to use agents | 先劝退 | 找最简单的可行方案，必要时才加复杂度，可能根本不该上 agent |
| When and how to use frameworks | 工具观 | 框架的抽象层有代价，先用 API 直连，用框架要读懂底层 |
| Building blocks, workflows, and agents | 正文主体 | 增强型 LLM 积木起步，五种 workflow 模式，最终到 agents |
| Combining and customizing | 边界声明 | 模式可组合可改造，度量驱动迭代 |
| Summary | 三原则收束 | 简单、透明、打磨 ACI |
| Appendix 2 | 隐藏主贡献 | ACI：把人机接口的功夫镜像到 agent 与计算机之间 |

目录从积木到系统的复杂度递增顺序本身就是叙事：读者按顺序读下来，每一步只比上一步复杂一点，最后到达 agents 时已经有了全部前置概念。这个结构与 Karpathy 训练配方文（先搭骨架再逐项复杂化）同构。

## 三、定义先行：workflows 与 agents 的二分法

第一节就把术语切干净：agentic systems 是总称，其下分两类。workflows 指 LLM 和工具通过预定义代码路径编排的系统；agents 指 LLM 动态主导自身流程与工具使用、对完成任务的方式保有控制权的系统。

这个二分的实用价值在决策：workflows 用延迟和成本换性能可控，适合边界清晰的任务；agents 适合无法预测步骤数的开放问题。后面所有模式的归位都依赖这组定义。写方法论文章先占住定义权，是这篇的第一个结构武器。

## 四、五种工作流模式：GoF 设计模式的体例

正文主体是五种 workflow 模式，每个模式都按同一套体例写：名字、一句话机制、When to use、两个例子。这种写法直接对标 GoF 设计模式手册，效果是模式可以被名字引用：「这个需求用 orchestrator-workers 就够了」成为团队内的可传播语言。

| 模式 | 一句话机制 | 适用信号 |
| --- | --- | --- |
| Prompt chaining | 任务拆成串行步骤，上一步输出喂下一步，中间可加程序性检查门 | 任务能干净地拆成固定子任务 |
| Routing | 先分类输入，再导向专门的下游提示 | 输入类别分明，分开优化互不干扰 |
| Parallelization | 子任务并行跑再程序化聚合，分 sectioning 与 voting 两个变体 | 子任务独立，或需要多视角提高置信 |
| Orchestrator-workers | 中央 LLM 动态拆解任务、分派工人、汇总结果 | 子任务数与内容无法预先确定 |
| Evaluator-optimizer | 一个 LLM 生成，另一个评估给反馈，循环迭代 | 有清晰评估标准，迭代有可度量收益 |

<figure style="margin:28px 0">
<svg viewBox="0 0 680 428" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs><marker id="an-a" markerWidth="6" markerHeight="6" refX="4.5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#57606a"/></marker></defs>
  <path d="M 30 400 L 650 30" stroke="#eaeef2" stroke-width="2" stroke-dasharray="6 5"/>
  <text x="648" y="22" font-size="10.5" fill="#8b949e" text-anchor="end">复杂度递增 →</text>
  <g font-size="11">
    <rect x="20" y="30" width="205" height="128" rx="10" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="32" y="52" font-size="12" font-weight="700" fill="#24292f">① 增强型 LLM</text>
    <rect x="90" y="64" width="66" height="20" rx="5" fill="#fff" stroke="#56B4E9"/><text x="123" y="78" text-anchor="middle" font-size="10" fill="#1E88B8">LLM</text>
    <g fill="#fff" stroke="#8b949e"><rect x="42" y="112" width="44" height="18" rx="4"/><rect x="102" y="112" width="44" height="18" rx="4"/><rect x="162" y="112" width="44" height="18" rx="4"/></g>
    <g font-size="9.5" fill="#57606a" text-anchor="middle"><text x="64" y="125">检索</text><text x="124" y="125">工具</text><text x="184" y="125">记忆</text></g>
    <text x="123" y="150" text-anchor="middle" font-size="10" fill="#8b949e">一切模式的积木</text>
    <rect x="240" y="30" width="205" height="128" rx="10" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="252" y="52" font-size="12" font-weight="700" fill="#24292f">② Prompt chaining</text>
    <g fill="#fff" stroke="#56B4E9"><rect x="252" y="78" width="44" height="20" rx="5"/><rect x="320" y="78" width="44" height="20" rx="5"/><rect x="388" y="78" width="44" height="20" rx="5"/></g>
    <g font-size="9.5" fill="#1E88B8" text-anchor="middle"><text x="274" y="92">LLM</text><text x="342" y="92">LLM</text><text x="410" y="92">LLM</text></g>
    <line x1="296" y1="88" x2="318" y2="88" stroke="#57606a" stroke-width="1.2" marker-end="url(#an-a)"/>
    <line x1="364" y1="88" x2="386" y2="88" stroke="#57606a" stroke-width="1.2" marker-end="url(#an-a)"/>
    <rect x="352" y="104" width="20" height="12" rx="3" fill="#fdf8ef" stroke="#E69F00"/><text x="362" y="113" text-anchor="middle" font-size="8.5" fill="#B77500">门</text>
    <text x="342" y="150" text-anchor="middle" font-size="10" fill="#8b949e">固定子任务串行 · 中间加检查门</text>
    <rect x="460" y="30" width="205" height="128" rx="10" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="472" y="52" font-size="12" font-weight="700" fill="#24292f">③ Routing</text>
    <rect x="510" y="64" width="52" height="20" rx="5" fill="#fff" stroke="#8b949e"/><text x="536" y="78" text-anchor="middle" font-size="9.5" fill="#57606a">输入</text>
    <g fill="#fff" stroke="#56B4E9"><rect x="472" y="108" width="52" height="18" rx="4"/><rect x="536" y="108" width="52" height="18" rx="4"/><rect x="600" y="108" width="52" height="18" rx="4"/></g>
    <g font-size="9" fill="#1E88B8" text-anchor="middle"><text x="498" y="121">提示 A</text><text x="562" y="121">提示 B</text><text x="626" y="121">提示 C</text></g>
    <path d="M 536 84 L 498 105" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <path d="M 536 84 L 562 105" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <path d="M 536 84 L 626 105" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <text x="562" y="150" text-anchor="middle" font-size="10" fill="#8b949e">输入类别分明 · 分开优化</text>
    <rect x="20" y="175" width="205" height="128" rx="10" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="32" y="197" font-size="12" font-weight="700" fill="#24292f">④ Parallelization</text>
    <rect x="32" y="215" width="52" height="20" rx="5" fill="#fff" stroke="#8b949e"/><text x="58" y="229" text-anchor="middle" font-size="9.5" fill="#57606a">输入</text>
    <g fill="#fff" stroke="#56B4E9"><rect x="100" y="207" width="40" height="18" rx="4"/><rect x="100" y="231" width="40" height="18" rx="4"/><rect x="100" y="255" width="40" height="18" rx="4"/></g>
    <g font-size="9" fill="#1E88B8" text-anchor="middle"><text x="120" y="220">LLM</text><text x="120" y="244">LLM</text><text x="120" y="268">LLM</text></g>
    <rect x="162" y="231" width="50" height="18" rx="4" fill="#fdf8ef" stroke="#E69F00"/><text x="187" y="244" text-anchor="middle" font-size="9" fill="#B77500">聚合</text>
    <path d="M 84 225 L 98 216" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <path d="M 84 225 L 98 240" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <path d="M 84 225 L 98 264" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <line x1="140" y1="240" x2="160" y2="240" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <text x="122" y="295" text-anchor="middle" font-size="10" fill="#8b949e">sectioning / voting 两变体</text>
    <rect x="240" y="175" width="205" height="128" rx="10" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="252" y="197" font-size="12" font-weight="700" fill="#24292f">⑤ Orchestrator-workers</text>
    <rect x="296" y="208" width="92" height="20" rx="5" fill="#fdf8ef" stroke="#E69F00" stroke-width="1.3"/><text x="342" y="222" text-anchor="middle" font-size="9.5" fill="#B77500">Orchestrator</text>
    <g fill="#fff" stroke="#56B4E9"><rect x="252" y="256" width="46" height="18" rx="4"/><rect x="319" y="256" width="46" height="18" rx="4"/><rect x="386" y="256" width="46" height="18" rx="4"/></g>
    <g font-size="9" fill="#1E88B8" text-anchor="middle"><text x="275" y="269">worker</text><text x="342" y="269">worker</text><text x="409" y="269">worker</text></g>
    <path d="M 320 228 L 280 253" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <path d="M 342 228 L 342 253" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <path d="M 364 228 L 404 253" stroke="#57606a" stroke-width="1" marker-end="url(#an-a)"/>
    <text x="342" y="295" text-anchor="middle" font-size="10" fill="#8b949e">子任务现场决定 · 数量不定</text>
    <rect x="460" y="175" width="205" height="128" rx="10" fill="#f6f8fa" stroke="#d0d7de"/>
    <text x="472" y="197" font-size="12" font-weight="700" fill="#24292f">⑥ Evaluator-optimizer</text>
    <rect x="472" y="222" width="80" height="22" rx="5" fill="#fff" stroke="#56B4E9"/><text x="512" y="237" text-anchor="middle" font-size="9.5" fill="#1E88B8">生成 LLM</text>
    <rect x="574" y="222" width="80" height="22" rx="5" fill="#f2fbf7" stroke="#009E73"/><text x="614" y="237" text-anchor="middle" font-size="9.5" fill="#00805C">评估 LLM</text>
    <path d="M 552 226 C 564 212, 580 212, 590 220" fill="none" stroke="#57606a" stroke-width="1.1" marker-end="url(#an-a)"/>
    <path d="M 590 244 C 578 258, 562 258, 552 250" fill="none" stroke="#009E73" stroke-width="1.1" marker-end="url(#an-a)"/>
    <text x="571" y="208" text-anchor="middle" font-size="9" fill="#8b949e">产出</text>
    <text x="571" y="272" text-anchor="middle" font-size="9" fill="#00805C">反馈</text>
    <text x="562" y="295" text-anchor="middle" font-size="10" fill="#8b949e">有清晰评估标准 · 循环迭代</text>
  </g>
  <rect x="20" y="322" width="645" height="66" rx="10" fill="#f2fbf7" stroke="#009E73" stroke-width="1.4"/>
  <text x="36" y="346" font-size="12.5" font-weight="700" fill="#00805C">Agents：LLM 在循环里基于环境反馈调用工具</text>
  <rect x="300" y="332" width="72" height="20" rx="5" fill="#fff" stroke="#56B4E9"/><text x="336" y="346" text-anchor="middle" font-size="10" fill="#1E88B8">LLM</text>
  <rect x="500" y="332" width="100" height="20" rx="5" fill="#fff" stroke="#E69F00"/><text x="550" y="346" text-anchor="middle" font-size="10" fill="#B77500">环境 · 工具</text>
  <path d="M 372 338 C 436 328, 460 328, 497 338" fill="none" stroke="#57606a" stroke-width="1.2" marker-end="url(#an-a)"/>
  <path d="M 497 350 C 436 360, 460 360, 372 350" fill="none" stroke="#009E73" stroke-width="1.2" marker-end="url(#an-a)"/>
  <text x="436" y="326" text-anchor="middle" font-size="9" fill="#8b949e">动作</text>
  <text x="436" y="372" text-anchor="middle" font-size="9" fill="#00805C">ground truth 反馈</text>
  <text x="36" y="372" font-size="10.5" fill="#57606a">停止条件（最大迭代数）保住控制权 · workflows 是预定义路径，agents 是 LLM 主导流程</text>
  <text x="342" y="416" font-size="10" fill="#8b949e" text-anchor="middle">五种模式与 agents 的复杂度阶梯仿绘 · 体例对标 GoF 设计模式手册（名字 · 机制 · 适用信号 · 例子）</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">复杂度阶梯仿绘：从增强型 LLM 积木出发，五种 workflow 模式按复杂度递增排列，终点是自主循环的 agents</figcaption>
</figure>

Orchestrator-workers 与 parallelization 的辨析最能见功力：两者形似，差别在于子任务是否预定义。前者的子任务由编排者按输入现场决定，后者先切好再跑。一句话把最容易被混淆的边界讲清。

Agents 一节收在一句金句上：agent 通常就是 LLM 基于环境反馈在循环里调用工具。循环内每一步都要从环境拿到 ground truth（工具调用结果、代码执行输出）评估进展，配停止条件（最大迭代数）保住控制权。例子来自他们自己的实现：解 SWE-bench 的 coding agent 与 computer use 参考实现。

## 五、Appendix 2 是全文最被低估的贡献

正文的 Summary 三原则里藏了一句：通过充分的工具文档与测试仔细打磨 agent-computer interface（ACI）。附录 2 展开了这个概念，核心类比是：人类在人机接口（HCI）上投入多少功夫，就该在 agent 与计算机的接口上投入同等的功夫。

四条实操建议：站在模型的角度检查工具描述是否自明；把参数命名当成给初级工程师写 docstring 来打磨；在工作台里跑大量样例观察模型怎么用错；给工具做防错设计（poka-yoke），让错误难以发生。

最有分量的证据是他们的 SWE-bench agent 实测：花在优化工具上的时间超过优化提示词的时间。典型案例是模型在离开根目录后会误用相对路径，把工具参数改成强制绝对路径后问题消失。一个具体到令人信服的工程细节，撑起一个概念。

<figure style="margin:28px 0">
<svg viewBox="0 0 680 252" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <line x1="340" y1="20" x2="340" y2="200" stroke="#d0d7de" stroke-dasharray="5 4"/>
  <text x="340" y="14" text-anchor="middle" font-size="10.5" fill="#8b949e">镜像类比</text>
  <rect x="28" y="28" width="280" height="168" rx="10" fill="#f6f8fa" stroke="#8b949e" stroke-opacity=".5"/>
  <text x="168" y="54" text-anchor="middle" font-size="13" font-weight="700" fill="#57606a">HCI · 人机接口</text>
  <g font-size="11" fill="#57606a">
    <text x="48" y="84">□ 界面文案让用户自明</text>
    <text x="48" y="112">□ 控件命名像产品文档</text>
    <text x="48" y="140">□ 观察真实用户操作</text>
    <text x="48" y="168">□ 防错设计让误操作难以发生</text>
  </g>
  <rect x="372" y="28" width="280" height="168" rx="10" fill="#f2fbf7" stroke="#009E73" stroke-opacity=".5"/>
  <text x="512" y="54" text-anchor="middle" font-size="13" font-weight="700" fill="#00805C">ACI · agent-计算机接口</text>
  <g font-size="11" fill="#3d6b5c">
    <text x="392" y="84">□ 工具描述站在模型角度是否自明</text>
    <text x="392" y="112">□ 参数命名当 docstring 打磨</text>
    <text x="392" y="140">□ 工作台跑大量样例看模型怎么用错</text>
    <text x="392" y="168">□ poka-yoke：参数强制绝对路径</text>
  </g>
  <path d="M 308 112 C 324 112, 328 112, 340 112 C 352 112, 356 112, 368 112" fill="none" stroke="#8b949e" stroke-width="1.2"/>
  <text x="340" y="222" text-anchor="middle" font-size="10.5" fill="#8b949e">SWE-bench 实测证据：花在优化工具上的时间 &gt; 花在优化提示词上的时间</text>
  <text x="340" y="242" text-anchor="middle" font-size="10.5" fill="#8b949e">相对路径误用 → 强制绝对路径后问题消失：一个工程细节撑起一个概念</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">ACI 镜像类比仿绘：把 HCI 的功夫原样镜像到 agent 与工具的接口上，四条建议左右一一对应</figcaption>
</figure>


## 六、能学走的三个写作技巧

1. **劝退前置**：把「何时不用」放在第二节，先劝退再教学，信任感来自克制而非推销
2. **模式命名体例**：名字、机制、适用信号、例子四件套统一，让读者能用名字引用你的内容
3. **附录放真货**：正文管传播，附录管深度，ACI 这种实操干货放附录反而增加全文的可信厚度

## 尾注：对我自己工作的映射

赛后教练系统的设计可以直接套用这篇的框架：六环节 pipeline 的顺序是预定义代码路径，系统整体属于 workflow；让 LLM 端到端自由发挥才叫 agent，当前阶段明确选前者，与「算法层做结构化、LLM 层做转述」的职责分离原则完全一致。结构化 JSON 接口的设计就是 ACI 思想的落地：字段名自明、边界清楚、防错优先。改善验证环节天然是 evaluator-optimizer 模式：行为改善的判据先于建议存在。

## 参考

- 原文：Building Effective Agents，Anthropic Engineering Blog，2024-12-19，anthropic.com/engineering/building-effective-agents
- 原文执笔：Erik Schluntz、Barry Zhang（据原文 Acknowledgements）
- 关联拆解：本博客 WebRL 拆解（用 RL 让模型学会任务分解，即 Anthropic 框架里从 workflow 走向 agent 的训练路线）、Search-R1 拆解（loss masking 属于工具接口的防错设计）
