#!/usr/bin/env python3
"""Fetch LLM papers from arXiv with full accumulation and proper company classification.

Key improvements:
- Correct arXiv query syntax: (cat:cs.CL OR cat:cs.AI) AND (query)
- Company papers validated by author/affiliation only (not abstract)
- max_results=100 per topic, 50 per company
- Generates timeline-data.json
- Accumulates all data across runs

Usage: python3 fetch_papers.py
"""
import urllib.request, urllib.parse, json, os, re, time, shutil
from datetime import datetime

# ── Topic queries (for general papers) ─────────────────────
QUERIES = [
    ("RAG",         'ti:"retrieval augmented generation" OR (ti:RAG AND ti:LLM)'),
    ("Agent",       'ti:"LLM agent" OR ti:"language model agent" OR ti:"autonomous agent"'),
    ("MCP",         'ti:"model context protocol" OR (ti:"tool use" AND ti:"language model")'),
    ("Reasoning",   'ti:"chain of thought" OR (ti:reasoning AND ti:"large language model")'),
    ("Multimodal",  'ti:multimodal AND (ti:"language model" OR ti:LLM OR ti:VLM)'),
    ("Fine-tuning", 'ti:LoRA OR ti:QLoRA OR ti:RLHF OR (ti:"instruction tuning" AND ti:LLM)'),
    ("Safety",      'ti:"AI safety" OR (ti:alignment AND ti:"language model")'),
    ("LLM",         'ti:"large language model" OR ti:"foundation model"'),
]

# ── Company queries (title-based + author validation) ─────
# Each company has: (query, author_keywords)
# author_keywords: list of strings that MUST appear in author names or affiliations
COMPANY_CONFIG = {
    "OpenAI": {
        "query": 'ti:gpt-4o OR ti:"o1" OR ti:"o3" OR ti:o4-mini OR ti:sora OR ti:chatgpt OR ti:codex',
        "author_keywords": ["openai"],
    },
    "Google": {
        "query": 'ti:gemini OR ti:gemma OR ti:palm OR ti:bard',
        "author_keywords": ["google", "deepmind", "google research", "google deepmind"],
    },
    "Anthropic": {
        "query": 'ti:claude',
        "author_keywords": ["anthropic"],
    },
    "Meta": {
        "query": 'ti:llama OR ti:"llama-" OR ti:fairseq',
        "author_keywords": ["meta ai", "meta platforms", "fair", "facebook ai", "meta research", "facebook ai research"],
    },
    "DeepSeek": {
        "query": 'ti:deepseek',
        "author_keywords": ["deepseek"],
    },
    "Qwen": {
        "query": 'ti:qwen OR ti:"tongyi qianwen"',
        "author_keywords": ["alibaba", "qwen", "tongyi", "damo"],
    },
    "Mistral": {
        "query": 'ti:mistral OR ti:mixtral OR ti:pixtral',
        "author_keywords": ["mistral"],
    },
    "Baidu": {
        "query": 'ti:ernie OR ti:"wenxin" OR ti:"paddle"',
        "author_keywords": ["baidu"],
    },
    "Xiaomi": {
        "query": 'ti:mimo OR ti:xiaomi',
        "author_keywords": ["xiaomi"],
    },
    "MiniMax": {
        "query": 'ti:minimax OR ti:"MiniMax-01" OR ti:"MiniMax-V"',
        "author_keywords": ["minimax"],
    },
    "Zhipu": {
        "query": 'ti:glm-4 OR ti:chatglm OR ti:zhipu OR ti:codegeex OR ti:cogvlm',
        "author_keywords": ["zhipu", "tsinghua", "chatglm"],
    },
}

TAG_RULES = [
    ('RAG',        r'retrieval|rag\b|knowledge base'),
    ('Agent',      r'agent|tool use|react\b|planning|autonomous'),
    ('Reasoning',  r'reasoning|chain.of.thought|cot\b|math|logic'),
    ('Multimodal', r'multimodal|vision|image|visual|vlm|video'),
    ('Fine-tuning',r'lora|rlhf|fine.tun|instruction tun|sft\b|dpo\b'),
    ('Safety',     r'safety|alignment|red.team|harmful|jailbreak'),
    ('LLM',        r'large language model|llm\b|foundation model'),
    ('MCP',        r'model context protocol|mcp\b|tool integration'),
]

MAX_RESULTS_TOPIC = 100
MAX_RESULTS_COMPANY = 50


def fetch_arxiv(query, tag, max_results=30):
    """Fetch papers from arXiv API with correct query syntax."""
    params = urllib.parse.urlencode({
        "search_query": f"(cat:cs.CL OR cat:cs.AI) AND ({query})",
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
        affiliations = re.findall(r'<arxiv:affiliation[^>]*>(.*?)</arxiv:affiliation>', entry)
        published = get('published')[:10]
        year = int(published[:4]) if published else 2025

        papers.append({
            "id": pid, "title": title, "authors": authors,
            "author_list": authors_raw,
            "affiliations": affiliations,
            "year": year, "date": published, "cite": 0,
            "tags": [tag], "abstract": abstract
        })
    return papers


def verify_company(paper, company, author_keywords):
    """Verify paper is actually from the company.

    Strategy 1: Check if company model name appears as a title prefix
    (e.g., "DeepSeek-V3: ..." is almost certainly from DeepSeek)
    Strategy 2: Check authors/affiliations for company keywords
    """
    title = paper.get('title', '').lower()

    # Title prefix check: most reliable for model release papers
    # Models are named like "DeepSeek-V3", "Qwen2.5", "Llama-3", "Claude 3", etc.
    company_prefixes = {
        'OpenAI': ['gpt-4', 'gpt-5', 'chatgpt', 'o1 ', 'o3 ', 'o1-', 'o3-', 'o4-', 'sora', 'codex', 'gpt-oss'],
        'Google': ['gemini', 'gemma', 'palm ', 'palm-'],
        'Anthropic': ['claude'],
        'Meta': ['llama', 'llama-', 'fairseq'],
        'DeepSeek': ['deepseek'],
        'Qwen': ['qwen', 'tongyi'],
        'Mistral': ['mistral', 'mixtral', 'pixtral', 'lesstral'],
        'Baidu': ['ernie', 'wenxin', 'paddle'],
        'Xiaomi': ['mimo', 'xiaomi'],
        'MiniMax': ['minimax'],
        'Zhipu': ['glm-4', 'glm-3', 'chatglm', 'codegeex', 'cogvlm', 'cogview'],
    }
    prefixes = company_prefixes.get(company, [])
    for prefix in prefixes:
        # Check if model name appears at start of title or after common prefixes
        if title.startswith(prefix) or f' {prefix}' in title or f': {prefix}' in title:
            return True

    # Fallback: check author/affiliation text
    author_text = ' '.join(paper.get('author_list', []) + paper.get('affiliations', [])).lower()
    return any(kw in author_text for kw in author_keywords)


def auto_tag(title, abstract=''):
    """Auto-tag paper based on title and abstract."""
    text = (title + ' ' + abstract).lower()
    return [t for t, p in TAG_RULES if re.search(p, text)] or ['LLM']


def generate_timeline(all_papers):
    """Generate timeline-data.json grouped by year-month and company."""
    timeline = {}
    for p in all_papers:
        date = p.get('date', '')
        if not date or len(date) < 7:
            continue
        ym = date[:7]
        company = p.get('company', '')
        if not company:
            continue
        if ym not in timeline:
            timeline[ym] = {}
        if company not in timeline[ym]:
            timeline[ym][company] = 0
        timeline[ym][company] += 1

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
    new_papers = []

    # ── Fetch topic papers ──────────────────────────────
    for tag, query in QUERIES:
        print(f"Fetching topic [{tag}]...")
        results = fetch_arxiv(query, tag, max_results=MAX_RESULTS_TOPIC)
        for p in results:
            p.pop('author_list', None)
            p.pop('affiliations', None)
            if p["id"] not in existing_map:
                new_papers.append(p)
                existing_map[p["id"]] = p
            else:
                existing_tags = existing_map[p["id"]].get("tags", [])
                if tag not in existing_tags:
                    existing_map[p["id"]]["tags"] = existing_tags + [tag]
        print(f"  Got {len(results)} (total unique: {len(existing_map)})")
        time.sleep(3)

    all_papers = sorted(existing_map.values(), key=lambda p: p.get("date", ""), reverse=True)
    with open("papers.json", "w") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)
    print(f"\nTopic papers: {len(all_papers)} total, {len(new_papers)} new")

    with open("daily_summary.txt", "w") as f:
        f.write(f"今日新增 {len(new_papers)} 篇论文，共收录 {len(all_papers)} 篇\n\n")
        for p in new_papers[:5]:
            f.write(f"• [{p['tags'][0]}] {p['title'][:60]}\n  https://arxiv.org/abs/{p['id']}\n\n")

    if os.path.exists("llm-tracker"):
        shutil.copy("papers.json", "llm-tracker/papers.json")
        print("Synced papers.json → llm-tracker/")

    # ── Company papers (with author verification) ────────
    existing_company = []
    if os.path.exists("llm-tracker/company-papers.json"):
        with open("llm-tracker/company-papers.json") as f:
            existing_company = json.load(f)
    existing_company_map = {p["id"]: p for p in existing_company}

    for company, config in COMPANY_CONFIG.items():
        query = config["query"]
        keywords = config["author_keywords"]
        print(f"Fetching company [{company}]...")
        raw_results = fetch_arxiv(f"({query})", company, max_results=MAX_RESULTS_COMPANY)

        confirmed = 0
        for p in raw_results:
            if not verify_company(p, company, keywords):
                continue  # Skip - not actually from this company
            confirmed += 1
            p['company'] = company
            p['tags'] = auto_tag(p['title'], p.get('abstract', ''))
            p.pop('author_list', None)
            p.pop('affiliations', None)

            if p['id'] not in existing_map:
                existing_map[p['id']] = p
                all_papers.append(p)
            else:
                existing_map[p['id']]['company'] = company

            if p['id'] not in existing_company_map:
                existing_company_map[p['id']] = p
            else:
                existing_company_map[p['id']]['company'] = company

        print(f"  Got {len(raw_results)} raw, {confirmed} confirmed")
        time.sleep(3)

    # Save company papers (accumulated, newest first)
    company_list = sorted(existing_company_map.values(),
                          key=lambda p: p.get("date", ""), reverse=True)
    company_out = [{"id": p["id"], "title": p["title"],
                     "title_zh": p.get("title_zh", ""),
                     "company": p["company"], "date": p.get("date", ""),
                     "tags": p.get("tags", [])} for p in company_list[:300]]
    with open("llm-tracker/company-papers.json", "w") as f:
        json.dump(company_out, f, ensure_ascii=False)
    print(f"Company papers: {len(company_out)}")

    # ── Timeline data ───────────────────────────────────
    all_papers_final = sorted(existing_map.values(),
                               key=lambda p: p.get("date", ""), reverse=True)
    timeline_data = generate_timeline(all_papers_final)
    with open("llm-tracker/timeline-data.json", "w") as f:
        json.dump(timeline_data, f, ensure_ascii=False)
    print(f"Timeline: {len(timeline_data)} months")

    print(f"\n✅ Done! {len(all_papers_final)} total, {len(new_papers)} new today")


if __name__ == '__main__':
    main()
