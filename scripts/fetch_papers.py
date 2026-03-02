import urllib.request, urllib.parse, json, os, re, time
from datetime import datetime

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

def fetch_arxiv(query, tag, max_results=30):
    params = urllib.parse.urlencode({
        "search_query": f"cat:cs.CL OR cat:cs.AI AND ({query})",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    })
    url = "http://export.arxiv.org/api/query?" + params
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
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
        if not m: continue
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

# Load existing
existing = []
if os.path.exists("papers.json"):
    with open("papers.json") as f:
        existing = json.load(f)

existing_map = {p["id"]: p for p in existing}
new_papers = []

for tag, query in QUERIES:
    print(f"Fetching [{tag}]...")
    results = fetch_arxiv(query, tag, max_results=30)
    for p in results:
        if p["id"] not in existing_map:
            new_papers.append(p)
            existing_map[p["id"]] = p
        else:
            # merge tags
            existing_tags = existing_map[p["id"]].get("tags", [])
            if tag not in existing_tags:
                existing_map[p["id"]]["tags"] = existing_tags + [tag]
    print(f"  Got {len(results)} papers, {sum(1 for p in results if p['id'] not in {x['id'] for x in existing})} new")
    time.sleep(3)  # be polite to arXiv

# Sort: newest first
all_papers = sorted(existing_map.values(), key=lambda p: p.get("date",""), reverse=True)

with open("papers.json", "w") as f:
    json.dump(all_papers, f, ensure_ascii=False, indent=2)

print(f"\nDone: {len(all_papers)} total, {len(new_papers)} new today")

with open("daily_summary.txt", "w") as f:
    f.write(f"今日新增 {len(new_papers)} 篇论文，共收录 {len(all_papers)} 篇\n\n")
    for p in new_papers[:5]:
        f.write(f"• [{p['tags'][0]}] {p['title'][:60]}\n  https://arxiv.org/abs/{p['id']}\n\n")

# sync to llm-tracker/
import shutil, os
if os.path.exists("llm-tracker"):
    shutil.copy("papers.json", "llm-tracker/papers.json")
    print("Synced to llm-tracker/papers.json")
