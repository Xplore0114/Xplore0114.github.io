---
layout:     post
title:      "OKC-SFT 复盘：把工业诊断大模型的幻觉率从 34.4% 压到 15.6%"
subtitle:   "操作知识链监督微调在空分装置异常处置上的一次完整实践"
date:       2026-08-25
author:     "Kevin"
header-img: "img/post-bg-2015.jpg"
catalog:    true
section:    实践复盘
tags:
    - LLM
    - 工业AI
---

> 本文复盘我一作论文 OKC-SFT 的完整实践：面向空分装置异常操作处置指令的结构化微调方法，论文投稿 CAC 2026，数据集已在 GitHub 开源（CC BY 4.0）。文中所有数字均可复现。

## 一、问题：工业场景容不下幻觉

空分装置（ASU）是流程工业的核心设备，操作工在异常工况下需要的是可立即执行的处置指令。让通用大模型回答「粗氩塔氮塞了怎么办」这类问题，答案往往读起来专业、细究全是错：编不存在的阀门位号、把处置顺序颠倒、漏掉必须停车的安全边界。

在聊天场景里，幻觉是体验问题；在工业处置场景里，幻觉是安全事故。这个项目要解决的只有一件事：让微调后的模型输出的每一条处置指令都可执行、可验证、有边界。

## 二、方法：把处置逻辑显式化为六元素链

分析优秀操作工的回答习惯后发现，合格的处置指令天然有一条完整的逻辑链。我们把它显式化为操作知识链（Operation Knowledge Chain，OKC）六元素，要求模型每次回答都必须输出全部六个字段：

| 字段 | 职责 |
| --- | --- |
| Diagnosis 诊断 | 判定异常状态与严重程度 |
| Evidence 证据 | 给出支撑判断的过程变量、设备状态、测量值 |
| Possible Causes 原因 | 解释因果机理与可能的故障源 |
| Operation Suggestions 操作 | 可执行的操作步骤 |
| Verification Indices 验证 | 操作后的监控变量与恢复判据 |
| Safety Notes 风险边界 | 何时减速、停车或上报升级 |

<figure style="margin:28px 0">
<svg viewBox="0 0 680 216" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <defs><marker id="ok-a" markerWidth="6" markerHeight="6" refX="4.5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#57606a"/></marker></defs>
  <g font-size="10.5" text-anchor="middle">
    <rect x="10" y="40" width="102" height="72" rx="9" fill="#f2fafd" stroke="#56B4E9" stroke-width="1.3"/>
    <text x="61" y="64" font-size="12" font-weight="700" fill="#1E88B8">① 诊断</text>
    <text x="61" y="84" fill="#57606a">Diagnosis</text>
    <text x="61" y="100" fill="#8b949e" font-size="9.5">异常状态与程度</text>
    <rect x="128" y="40" width="102" height="72" rx="9" fill="#f6f8fa" stroke="#8b949e" stroke-opacity=".6"/>
    <text x="179" y="64" font-size="12" font-weight="700" fill="#57606a">② 证据</text>
    <text x="179" y="84" fill="#57606a">Evidence</text>
    <text x="179" y="100" fill="#8b949e" font-size="9.5">过程变量 · 测量值</text>
    <rect x="246" y="40" width="102" height="72" rx="9" fill="#f6f8fa" stroke="#8b949e" stroke-opacity=".6"/>
    <text x="297" y="64" font-size="12" font-weight="700" fill="#57606a">③ 原因</text>
    <text x="297" y="84" fill="#57606a">Causes</text>
    <text x="297" y="100" fill="#8b949e" font-size="9.5">因果机理 · 故障源</text>
    <rect x="364" y="40" width="102" height="72" rx="9" fill="#f2fbf7" stroke="#009E73" stroke-width="1.3"/>
    <text x="415" y="64" font-size="12" font-weight="700" fill="#00805C">④ 操作</text>
    <text x="415" y="84" fill="#57606a">Operation</text>
    <text x="415" y="100" fill="#8b949e" font-size="9.5">可执行步骤</text>
    <rect x="482" y="40" width="102" height="72" rx="9" fill="#fdf8ef" stroke="#E69F00" stroke-width="1.3"/>
    <text x="533" y="64" font-size="12" font-weight="700" fill="#B77500">⑤ 验证</text>
    <text x="533" y="84" fill="#57606a">Verification</text>
    <text x="533" y="100" fill="#8b949e" font-size="9.5">监控变量 · 恢复判据</text>
    <rect x="600" y="40" width="70" height="72" rx="9" fill="#fdf3f1" stroke="#D55E00" stroke-width="1.3"/>
    <text x="635" y="64" font-size="12" font-weight="700" fill="#A0410A">⑥ 风险</text>
    <text x="635" y="84" fill="#57606a">Safety</text>
    <text x="635" y="100" fill="#8b949e" font-size="9.5">停车 · 上报</text>
  </g>
  <g>
    <line x1="112" y1="76" x2="126" y2="76" stroke="#57606a" stroke-width="1.3" marker-end="url(#ok-a)"/>
    <line x1="230" y1="76" x2="244" y2="76" stroke="#57606a" stroke-width="1.3" marker-end="url(#ok-a)"/>
    <line x1="348" y1="76" x2="362" y2="76" stroke="#57606a" stroke-width="1.3" marker-end="url(#ok-a)"/>
    <line x1="466" y1="76" x2="480" y2="76" stroke="#57606a" stroke-width="1.3" marker-end="url(#ok-a)"/>
    <line x1="584" y1="76" x2="598" y2="76" stroke="#57606a" stroke-width="1.3" marker-end="url(#ok-a)"/>
  </g>
  <text x="340" y="152" font-size="11.5" font-weight="600" fill="#24292f" text-anchor="middle">每次回答必须输出全部六字段：幻觉最容易发生在自由发挥处，槽位收窄了输出空间</text>
  <text x="340" y="176" font-size="10.5" fill="#8b949e" text-anchor="middle">无论问题类型是什么（哪怕只是问一个位号的含义），都走完全链，让结构成为肌肉记忆</text>
  <text x="340" y="200" font-size="10.5" fill="#8b949e" text-anchor="middle">缺了哪个字段，在评测端立刻可见 · 场景：空分装置粗氩塔氮塞处置</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">OKC 六元素链：处置逻辑显式化为六个必填槽位，从诊断一路锚定到风险边界</figcaption>
</figure>


核心思路：幻觉最容易发生在模型「自由发挥」的地方，六字段结构把回答的每一步都锚定在必须填充的槽位上，模型没有随意发挥的余地，缺了哪个字段在评测端立刻可见。

## 三、数据：611 条结构化样本与 858 条非结构化基线

为了证明增益来自结构而非数据量，我们构建了两组训练数据做对照，场景均为粗氩塔氮塞（nitrogen_plugging）：

| 数据集 | 样本数 | 形态 | 作用 |
| --- | --- | --- | --- |
| okc_sft_train.jsonl | 611 | 六字段结构化输出 | 实验组 |
| qa_sft_train.jsonl | 858 | 常规问答式输出 | 基线组 |
| test_set.jsonl | 61 | 六类任务均衡分布 | 评估集 |

三个设计细节值得记录：

1. **全字段输出**。OKC-SFT 的每条样本无论问题类型是什么，输出都必须是完整六字段。问「AI705 这个位号什么意思」，也要走完诊断到风险边界的全链，让结构成为肌肉记忆。
2. **来源可追溯**。每条样本的 metadata 带 source_trace，标记它来自哪条源问答、哪条知识链条目，数据出问题可以逐条回溯。
3. **评估集带关键点**。测试集不写标准答案全文，只写 expected_key_points（期望关键点），例如「AI705 表征粗氩纯度，持续下降是氮塞最核心的预警信号」，为自动评测留接口。

## 四、评测：三个指标构成的完整循环

工业问答没有现成基准，我们自建了评测循环，围绕三个指标：

| 指标 | 含义 | 目标方向 |
| --- | --- | --- |
| 结构完整率 | 输出是否包含全部六字段 | 越高越好 |
| 关键点覆盖率 | expected_key_points 被命中的比例 | 越高越好 |
| 幻觉率 | 输出中出现编造位号、错误操作、虚构机理的比例 | 越低越好 |

基座模型为 Qwen2.5-7B，LoRA 微调。先训基线组跑一轮评测，再训实验组跑同一套评测，两轮使用完全相同的测试集与评分口径，保证对比公平。

## 五、结果

| 指标 | QA-SFT 基线（858 条） | OKC-SFT（611 条） |
| --- | --- | --- |
| 幻觉率 | 34.4% | **15.6%** |
| 结构完整率 | 无结构约束 | 99.8% |
| 关键点覆盖率 | 低于实验组 | 0.7378 |

<figure style="margin:28px 0">
<svg viewBox="0 0 680 252" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
  <text x="30" y="24" font-size="12.5" font-weight="700" fill="#24292f">幻觉率：34.4% → 15.6%（同测试集 61 条 · 同评分口径）</text>
  <g stroke="#eaeef2"><line x1="60" y1="50" x2="420" y2="50"/><line x1="60" y1="100" x2="420" y2="100"/><line x1="60" y1="150" x2="420" y2="150"/><line x1="60" y1="200" x2="420" y2="200"/></g>
  <line x1="60" y1="205" x2="420" y2="205" stroke="#d0d7de"/>
  <g font-size="10" fill="#8b949e"><text x="54" y="204" text-anchor="end">0</text><text x="54" y="154" text-anchor="end">10</text><text x="54" y="104" text-anchor="end">20</text><text x="54" y="54" text-anchor="end">30</text></g>
  <g font-size="11.5" fill="#24292f"><text x="52" y="76" text-anchor="end">QA 基线</text><text x="52" y="136" text-anchor="end">OKC-SFT</text></g>
  <g>
    <rect x="60" y="58" width="331" height="22" rx="5" fill="#D55E00" fill-opacity=".85"/>
    <text x="398" y="74" font-size="12" font-weight="700" fill="#A0410A">34.4%</text>
    <rect x="60" y="118" width="150" height="22" rx="5" fill="#009E73"/>
    <text x="217" y="134" font-size="12" font-weight="700" fill="#00805C">15.6%</text>
  </g>
  <path d="M 391 69 C 420 90, 240 118, 216 126" fill="none" stroke="#009E73" stroke-width="1.6" stroke-dasharray="5 3"/>
  <text x="330" y="100" font-size="10.5" fill="#00805C" text-anchor="middle">下降超过一半</text>
  <g>
    <rect x="450" y="46" width="206" height="62" rx="10" fill="#f2fbf7" stroke="#009E73" stroke-opacity=".45"/>
    <text x="468" y="72" font-size="20" font-weight="700" fill="#00805C">99.8%</text>
    <text x="468" y="94" font-size="10.5" fill="#57606a">结构完整率 · 六字段格式稳定学会</text>
    <rect x="450" y="122" width="206" height="62" rx="10" fill="#f2fafd" stroke="#56B4E9" stroke-opacity=".45"/>
    <text x="468" y="148" font-size="20" font-weight="700" fill="#1E88B8">0.7378</text>
    <text x="468" y="170" font-size="10.5" fill="#57606a">关键点覆盖率 · expected_key_points</text>
  </g>
  <text x="340" y="228" font-size="10.5" fill="#8b949e" text-anchor="middle">Qwen2.5-7B · LoRA 微调 · 611 条结构化样本胜过 858 条非结构化基线，增益来自结构约束本身</text>
  <text x="340" y="246" font-size="10.5" fill="#8b949e" text-anchor="middle">残余 15.6% 如实写进论文，直接定义下一阶段（RAG + 审核流）的工作目标</text>
</svg>
<figcaption style="text-align:center;font-size:13px;color:#57606a;margin-top:10px">主结果重绘：幻觉率减半，结构完整率接近满分，更少的结构化数据赢了更多的非结构化数据</figcaption>
</figure>


三个值得强调的点：

1. **更少的结构化数据赢了更多的非结构化数据**。611 条对 858 条，幻觉率下降超过一半，说明增益来自结构约束本身。
2. **结构完整率接近满分**说明六字段格式被模型稳定学会，格式约束是零成本兑现的。
3. **幻觉率 15.6% 仍不达标**。工业上线还需要检索增强与人工审核兜底，论文也如实讨论了这一点。

## 六、经验总结

1. **结构即约束**。抑制幻觉最直接的手段是把输出空间收窄到必须填充的槽位上，这比堆数据、堆参数便宜得多。
2. **评测先于训练**。expected_key_points 与评分口径在训模型之前就定好，后面所有迭代都有统一的标尺，避免「感觉变好了」式开发。
3. **小数据垂直微调是可行的**。611 条高质量样本足以让 7B 模型学会一个工业场景的回答范式，前提是每条样本的格式与来源都严格受控。
4. **可追溯性救过命**。数据审查时发现的部分错误样本，全靠 source_trace 逐条定位回源问答修正，没有这套机制只能靠重读全量数据。
5. **诚实面对残余幻觉**。15.6% 写进论文比包装成 0% 更有价值，它直接定义了下一阶段（RAG + 审核流）的工作目标。

## 七、开源资源

- 数据集：[OKC-SFT-Dataset](https://github.com/Xplore-LAB/OKC-SFT-Dataset)（CC BY 4.0），含全部训练、基线与测试数据
- 格式兼容 LLaMA-Factory，拷入 data 目录即可开训
- 论文：投稿 CAC 2026，目前为单一场景（氮塞）验证，多场景扩展进行中

欢迎在 GitHub 提 Issue 交流。
