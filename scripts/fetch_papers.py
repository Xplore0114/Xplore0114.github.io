import urllib.request
import urllib.parse
import json
import os
import re
from datetime import datetime, timedelta

QUERIES = [
    ("RAG", "retrieval augmented generation LLM"),
    ("Agent", "LLM agent autonomous tool use"),
    ("MCP", "model context protocol tool integration"),
    ("Reasoning", "chain of thought reasoning large language model"),
    ("Multimodal", "multimodal large language model vision"),
    ("Fine-tuning", "LoRA RLHF instruction tuning LLM"),
    ("Safety", "LLM alignment safety harmlessness"),
    ("LLM", "large language model foundation model"),
]

def fetch_arxiv(query, tag, max_results=5):
    base = "http://export.arxiv.org/api/query?"
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    })
    url = base + params
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            content = r.read().decode()
    except Exception as e:
        print(f"Error fetching {tag}: {e}")
        return []

    papers = []
    entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
    for entry in entries:
        def get(field):
            m = re.search(rf'<{field}[^>]*>(.*?)</{field}>', entry, re.DOTALL)
            return m.group(1).strip() if m else ""
        
        arxiv_id = re.search(r'<id>.*?/abs/([^<]+)</id>', entry)
        if not arxiv_id:
            continue
        pid = arxiv_id.group(1).replace('\n','').strip()
        title = re.sub(r'\s+', ' ', get('title'))
        abstract = re.sub(r'\s+', ' ', get('summary'))[:400]
        authors_raw = re.findall(r'<name>(.*?)</name>', entry)
        authors = ', '.join(authors_raw[:3]) + (' et al.' if len(authors_raw) > 3 else '')
        published = get('published')[:10]
        year = int(published[:4]) if published else 2025

        papers.append({
            "id": pid,
            "title": title,
            "authors": authors,
            "year": year,
            "date": published,
            "cite": 0,
            "tags": [tag],
            "abstract": abstract
        })
    return papers

# Load existing papers
existing_file = "papers.json"
existing = []
if os.path.exists(existing_file):
    with open(existing_file) as f:
        existing = json.load(f)

existing_ids = {p["id"] for p in existing}
new_papers = []

for tag, query in QUERIES:
    results = fetch_arxiv(query, tag)
    for p in results:
        if p["id"] not in existing_ids:
            new_papers.append(p)
            existing_ids.add(p["id"])
            print(f"NEW [{tag}]: {p['title'][:60]}")

# Merge: new papers first, keep max 200
all_papers = new_papers + existing
all_papers = all_papers[:200]

with open(existing_file, "w") as f:
    json.dump(all_papers, f, ensure_ascii=False, indent=2)

print(f"\nTotal: {len(all_papers)} papers, {len(new_papers)} new today")

# Write summary for notification
with open("daily_summary.txt", "w") as f:
    f.write(f"今日新增 {len(new_papers)} 篇论文\n\n")
    for p in new_papers[:5]:
        f.write(f"• [{p['tags'][0]}] {p['title'][:60]}\n  https://arxiv.org/abs/{p['id']}\n\n")
