#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))

ITEMS = [
    {
        "title": "主页",
        "path": "/",
        "group": "站点",
        "emoji": "🏠",
        "badge": "Home",
        "desc": "个人主页与最新动态总入口",
        "featured": True,
    },
    {
        "title": "LLM Papers Tracker",
        "path": "/llm-tracker/",
        "group": "AI 项目",
        "emoji": "🤖",
        "badge": "Active",
        "desc": "LLM 论文追踪主页面，支持检索和多维筛选",
        "featured": True,
    },
    {
        "title": "LLM 时间轴",
        "path": "/llm-tracker/timeline/",
        "group": "AI 项目",
        "emoji": "📅",
        "badge": "Timeline",
        "desc": "按时间查看论文趋势、热度和主题分布",
        "featured": True,
    },
    {
        "title": "关于",
        "path": "/about/",
        "group": "站点",
        "emoji": "🙋",
        "badge": "About",
        "desc": "查看个人介绍、合作方向与联系方式",
    },
    {
        "title": "标签",
        "path": "/tags/",
        "group": "站点",
        "emoji": "🏷️",
        "badge": "Tags",
        "desc": "浏览全部文章标签并按主题筛选内容",
    },
    {
        "title": "GitHub 主页",
        "path": "https://github.com/Xplore0114",
        "group": "外部链接",
        "emoji": "🐙",
        "badge": "External",
        "desc": "查看完整仓库列表与开源动态",
    },
    {
        "title": "system-prompts-and-models-of-ai-tools",
        "path": "https://github.com/Xplore0114/system-prompts-and-models-of-ai-tools",
        "group": "仓库",
        "emoji": "🧠",
        "badge": "Repo",
        "desc": "系统提示词与模型资料归档项目",
    },
    {
        "title": "zotero-arxiv-daily",
        "path": "https://github.com/Xplore0114/zotero-arxiv-daily",
        "group": "仓库",
        "emoji": "📚",
        "badge": "Repo",
        "desc": "面向 Zotero 的 arXiv 每日推荐项目",
    },
    {
        "title": "py-nl2sql",
        "path": "https://github.com/Xplore0114/py-nl2sql",
        "group": "仓库",
        "emoji": "🛠️",
        "badge": "Repo",
        "desc": "自然语言转 SQL 的工具链与实验仓库",
    },
]

payload = {
    "generated_at": datetime.now(TZ).replace(microsecond=0).isoformat(),
    "items": ITEMS,
}

with open("site-nav/routes.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"site-nav/routes.json updated: {len(ITEMS)} items")
