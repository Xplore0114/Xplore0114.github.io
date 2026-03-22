#!/usr/bin/env python3
"""Fetch LLM papers from arXiv with full accumulation.

Key improvements over original:
- max_results=100 per query (vs 30) to catch more papers
- Company papers properly accumulated across runs
- Generates timeline-data.json for the timeline page
- Better error handling and logging

Usage: python3 fetch_papers.py
Requires: GITHUB_PAT env var (for nothing in this script, but used by workflow)
"""
import urllib.request, urllib.parse, json, os, re, time, shutil
from datetime import datetime

# ── Topic queries ──────────────────────────────────────────
QUERIES = [
    ("RAG",         'ti:"retrieval augmented generation" OR ti:RAG AND ti:LLM'),
    ("Agent",       'ti:"LLM agent" OR ti:"language model agent" OR ti:"autonomous agent"'),
    ("MCP",         'ti:"model context protocol" OR (ti:"tool use" AND ti:"language model")'),
    ("Reasoning",   'ti:"chain of thought" OR ti:"reasoning" AND ti:"large language model"'),
    ("Multimodal",  'ti:"multimodal" AND (ti:"language model" OR ti:LLM OR ti:VLM)'),
    ("Fine-tuning", 'ti:LoRA OR ti:QLoRA OR ti:RLHF OR (ti:"instruction tuning" AND ti:LLM)'),
    ("Safety",      'ti:"AI safety" OR ti:"alignment" AND ti:"language model" OR ti:"harmless"'),
    ("LLM",         'ti:"large language model" OR ti:"foundation model" OR ti:"language model"'),
]

COMPANY_QUERIES = [
    ("OpenAI",    'au:openai'),
    ("Google",    'au:google AND (cat:cs.CL OR cat:cs.AI)'),
    ("Meta",      'au:meta AND ti:llama'),
    ("Mistral",   'ti:mistral OR au:mistral'),
    ("Qwen",      'ti:qwen OR au:alibaba AND cat:cs.CL'),
    ("DeepSeek",  'ti:deepseek OR au:deepseek'),
    ("Anthropic", 'au:anthropic'),
    ("Baidu",     'au:baidu AND (cat:cs.CL OR cat:cs.AI)'),
]

TAG_RULES = [
    ('RAG',        r'retrieval|rag\b|knowledge base'),
    ('Agent',      r'agent|tool use|react\b|planning|autonomous'),
    ('Reasoning',  r'reasoning|chain.of.thought|cot\b|math|logic'),
    ('Multimodal', r'multimodal|vision|image|visual|vlm|video'),
    ('Fine-tuning',r'lora|rlhf|fine.tun|instruction tun|sft\b|dpo\b'),
    ('Safety',     r'safety|alignment|red.team|harmful|jailbreak'),
    ('LLM',        r'large language model|llm\b|foundation model'),
    ('MCP',        r'model context protocol|mcp\b|tool use'),
]

MAX_RESULTS_TOPIC = 100   # per topic query
MAX_RESULTS_COMPANY = 50  # per company query


def fetch_arxiv(query, tag, max_results=30):
    """Fetch papers from arXiv API (HTTPS only)."""
    params = urllib.parse.urlencode({
        "search_query": f"cat:cs.CL OR cat:cs.AI AND ({query})",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    })
    url = "https://export.arxiv.org/api/query?" + params
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            content = r.read().decode()
    except Exception as e:
        print(f"  Error [{tag}]: {e}")
        return []

    papers = []
    for entry in re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL):
        def get(f):
            m = re.search(rf'<{f}[^>]*>(.*?)</{f}>', entry, re.DOTALL)
            return m.group(1).strip() if m else ""

        m = re.search(r'<id>.*?/abs/([^v<\n]+)', entry)
        if not m:
            continue
        pid = m.group(1).strip()
        title = re.sub(r'\s+', ' ', get('title'))
        abstract = re.sub(r'\s+', ' ', get('summary'))[:500]
        authors_raw = re.findall(r'<name>(.*?)</name>', entry)
        authors = ', '.join(authors_raw[:3]) + (' et al.' if len(authors_raw) > 3 else '')
        published = get('published')[:10]
        year = int(published[:4]) if published else 2025
        papers.append({
            "id": pid, "title": title, "authors": authors,
            "year": year, "date": published, "cite": 0,
            "tags": [tag], "abstract": abstract
        })
    return papers


def auto_tag(title, abstract=''):
    """Auto-tag paper based on title and abstract."""
    text = (title + ' ' + abstract).lower()
    return [t for t, p in TAG_RULES if re.search(p, text)] or ['LLM']


def generate_timeline(all_papers):
    """Generate timeline-data.json from all papers."""
    # Group papers by year-month
    timeline = {}
    for p in all_papers:
        date = p.get('date', '')
        if not date or len(date) < 7:
            continue
        ym = date[:7]  # "2026-03"
        company = p.get('company', '')
        if not company:
            continue
        if ym not in timeline:
            timeline[ym] = {}
        if company not in timeline[ym]:
            timeline[ym][company] = 0
        timeline[ym][company] += 1

    # Convert to sorted list
    result = []
    for ym in sorted(timeline.keys(), reverse=True):
        entry = {"month": ym}
        entry.update(timeline[ym])
        result.append(entry)

    return result


def main():
    print(f"[{datetime.now().isoformat()}] Starting paper fetch...")

    # ── Load existing papers ─────────────────────────────
    existing = []
    if os.path.exists("papers.json"):
        with open("papers.json") as f:
            existing = json.load(f)

    existing_map = {p["id"]: p for p in existing}
    existing_ids = set(existing_map.keys())
    new_papers = []

    # ── Fetch topic papers ──────────────────────────────
    for tag, query in QUERIES:
        print(f"Fetching [{tag}]...")
        results = fetch_arxiv(query, tag, max_results=MAX_RESULTS_TOPIC)
        for p in results:
            if p["id"] not in existing_map:
                new_papers.append(p)
                existing_map[p["id"]] = p
            else:
                existing_tags = existing_map[p["id"]].get("tags", [])
                if tag not in existing_tags:
                    existing_map[p["id"]]["tags"] = existing_tags + [tag]
        print(f"  Got {len(results)} papers (total unique: {len(existing_map)})")
        time.sleep(3)

    # ── Sort: newest first ──────────────────────────────
    all_papers = sorted(existing_map.values(), key=lambda p: p.get("date", ""), reverse=True)

    # ── Save papers.json ────────────────────────────────
    with open("papers.json", "w") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)
    print(f"\nTopic papers: {len(all_papers)} total, {len(new_papers)} new")

    # ── Daily summary ───────────────────────────────────
    with open("daily_summary.txt", "w") as f:
        f.write(f"今日新增 {len(new_papers)} 篇论文，共收录 {len(all_papers)} 篇\n\n")
        for p in new_papers[:5]:
            f.write(f"• [{p['tags'][0]}] {p['title'][:60]}\n  https://arxiv.org/abs/{p['id']}\n\n")

    # ── Sync to llm-tracker/ ───────────────────────────
    if os.path.exists("llm-tracker"):
        shutil.copy("papers.json", "llm-tracker/papers.json")
        print("Synced papers.json → llm-tracker/")

    # ── Company papers ──────────────────────────────────
    # Load existing company papers for accumulation
    existing_company = []
    if os.path.exists("llm-tracker/company-papers.json"):
        with open("llm-tracker/company-papers.json") as f:
            existing_company = json.load(f)
    existing_company_map = {p["id"]: p for p in existing_company}

    for company, query in COMPANY_QUERIES:
        print(f"Fetching company [{company}]...")
        results = fetch_arxiv(f"({query})", company, max_results=MAX_RESULTS_COMPANY)
        for p in results:
            p['company'] = company
            p['tags'] = auto_tag(p['title'], p.get('abstract', ''))
            # Update main papers list
            if p['id'] not in existing_map:
                existing_map[p['id']] = p
                all_papers.append(p)
            else:
                existing_map[p['id']]['company'] = company
            # Update company papers list
            if p['id'] not in existing_company_map:
                existing_company_map[p['id']] = p
            else:
                existing_company_map[p['id']]['company'] = company
                if not existing_company_map[p['id']].get('tags') or \
                   existing_company_map[p['id']]['tags'] == [company]:
                    existing_company_map[p['id']]['tags'] = p['tags']
        print(f"  Got {len(results)} papers")
        time.sleep(3)

    # Rebuild company-papers.json (all accumulated, newest first)
    company_list = sorted(existing_company_map.values(),
                          key=lambda p: p.get("date", ""), reverse=True)
    company_out = [{"id": p["id"], "title": p["title"],
                     "title_zh": p.get("title_zh", ""),
                     "company": p["company"], "date": p.get("date", ""),
                     "tags": p.get("tags", [])} for p in company_list[:200]]

    with open("llm-tracker/company-papers.json", "w") as f:
        json.dump(company_out, f, ensure_ascii=False)
    print(f"Company papers: {len(company_out)}")

    # ── Generate timeline data ──────────────────────────
    all_papers_final = sorted(existing_map.values(),
                               key=lambda p: p.get("date", ""), reverse=True)
    timeline_data = generate_timeline(all_papers_final)
    with open("llm-tracker/timeline-data.json", "w") as f:
        json.dump(timeline_data, f, ensure_ascii=False)
    print(f"Timeline: {len(timeline_data)} months")

    print(f"\n✅ Done! {len(all_papers_final)} total papers, {len(new_papers)} new today")


if __name__ == '__main__':
    main()
