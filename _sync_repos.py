#!/usr/bin/env python3
"""site-nav 自动同步：把用户自己创建的公开仓库自动挂到导航页。

- 数据源: GitHub REST API (users/{owner}/repos, 按最近推送排序)
- 过滤: 非 fork、非 private、排除与用户名同名的 profile 仓库
- 合并: 手写入口 (site-nav/_base.json) + 自动仓库卡片
- 输出: site-nav/routes.json (页面 index.html 直接读取)
- 幂等: 仓库列表无变化时不重写文件 (避免每天无意义提交)
"""
import json
import os
import sys
import urllib.request
from datetime import datetime

OWNER = os.environ.get("REPO_OWNER", "Xplore-LAB")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(HERE, "_base.json")
OUT_PATH = os.path.join(HERE, "site-nav", "routes.json")

# 语言 -> emoji 映射 (没有映射的用 📦)
LANG_EMOJI = {
    "Python": "🐍", "JavaScript": "🟨", "TypeScript": "🟦", "HTML": "🌐",
    "CSS": "🎨", "Dart": "📱", "VBA": "📧", "Shell": "🐚",
    "Jupyter Notebook": "📓", "C": "⚙️", "C++": "⚙️", "Rust": "🦀",
    "Go": "🐹", "Java": "☕", "Kotlin": "🟣", "Swift": "🍎",
    "Ruby": "💎", "PHP": "🐘", "Vue": "🖼️", "Dockerfile": "🐳",
    "Markdown": "📝", "PowerShell": "🪟", "Lua": "🌙", "R": "📊",
    "TeX": "📐", "SCSS": "🎨", "C#": "🔷", "Solidity": "⛓️",
}


def fetch_repos():
    url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=pushed"
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json", "User-Agent": "site-nav-sync"}
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


# 分组展示顺序（未匹配的组排最后）
GROUP_ORDER = ["站点", "大项目", "Agent 技能", "小工具", "推荐网站", "外部链接", "开源项目"]


def repo_to_item(r, name_to_group=None):
    lang = r.get("language") or ""
    desc = (r.get("description") or "").strip()
    group = (name_to_group or {}).get(r["name"], "开源项目")
    return {
        "desc": desc or "暂无描述，点击查看仓库详情",
        "badge": lang or "Repo",
        "featured": False,
        "path": r["html_url"],
        "emoji": LANG_EMOJI.get(lang, "📦"),
        "title": r["name"],
        "group": group,
    }


def main():
    with open(BASE_PATH, encoding="utf-8") as f:
        base = json.load(f)

    repos = [
        r for r in fetch_repos()
        if not r["fork"] and not r["private"] and r["name"] != OWNER
    ]
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)

    featured = set(base.get("featured_repos", []))
    desc_overrides = base.get("desc_overrides", {})
    repo_groups = base.get("repo_groups", {})
    name_to_group = {name: g for g, names in repo_groups.items() for name in names}
    auto_items = [repo_to_item(r, name_to_group) for r in repos]
    for item in auto_items:
        if item["title"] in featured:
            item["featured"] = True
        if item["title"] in desc_overrides:
            item["desc"] = desc_overrides[item["title"]]

    # 安全护栏：已映射且未声明私有的仓库必须全部抓到，否则判定 API 异常，终止而不覆盖现有文件
    private_repos = set(base.get("private_repos", []))
    expected = set(name_to_group.keys()) - private_repos
    fetched_names = {r["name"] for r in repos}
    missing = expected - fetched_names
    if missing:
        print(f"[site-nav] 抓取异常：缺失 {len(missing)}/{len(expected)} 个已映射仓库: {sorted(missing)}")
        print("[site-nav] 终止本次同步，不覆盖现有 routes.json")
        sys.exit(1)

    # 已声明私有的映射仓库：保留入口并标注「私有」，日后转公开自动恢复常规卡片
    for g in GROUP_ORDER:
        for name in repo_groups.get(g, []):
            if name in private_repos and name not in fetched_names:
                auto_items.append({
                    "desc": desc_overrides.get(name, "私有仓库，暂未公开"),
                    "badge": "私有",
                    "featured": False,
                    "path": f"https://github.com/{OWNER}/{name}",
                    "emoji": "🔒",
                    "title": name,
                    "group": g,
                })

    items = list(base.get("items", [])) + auto_items

    # 稳定排序：按 GROUP_ORDER 组序展示，组内保持原顺序
    order = {g: i for i, g in enumerate(GROUP_ORDER)}
    items.sort(key=lambda it: order.get(it.get("group"), len(order)))

    # 幂等检查：仓库列表没变就不动文件，避免每日无意义提交
    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH, encoding="utf-8") as f:
                old = json.load(f)
            if old.get("items") == items:
                print(f"[site-nav] 仓库列表无变化 ({len(items)} 个入口)，跳过写入")
                return
        except Exception:
            pass

    routes = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "items": items,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(routes, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print(f"[site-nav] 同步完成：{len(auto_items)} 个仓库，共 {len(items)} 个入口 → routes.json")


if __name__ == "__main__":
    main()
