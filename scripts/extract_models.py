#!/usr/bin/env python3
"""Extract model series and release timeline from company-papers.json.

Reads llm-tracker/company-papers.json (+ papers.json for notes), writes
llm-tracker/models.json:

{
  "models": [   # one entry per distinct model release, for the timeline
    {"model": "DeepSeek-V3", "company": "DeepSeek", "date": "2024-12-26",
     "id": "2412.19437", "title": "...", "note": "..."}
  ],
  "groups": [   # papers organized per company -> model series
    {"company": "DeepSeek",
     "series": [{"model": "DeepSeek-V3", "papers": [{id,title,date,note}]}],
     "others": [{id,title,date,note}]}
  ]
}
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER = os.path.join(ROOT, "llm-tracker")

# Per-company regex capturing the model name from a paper title.
# Applied to the ORIGINAL-case title; group 1 is the model name.
MODEL_PATTERNS = {
    "OpenAI":    r'\b(GPT-?[45](?:\.\d)?[a-z]?(?:-[\w.]+)?|GPT-oss(?:-\d+b)?|o[134](?:-(?:mini|pro))?|Sora|Codex)\b',
    "Google":    r'\b(Gemini\s?\d(?:\.\d)?(?:\s?(?:Pro|Flash|Ultra|Nano|Robotics))?|Gemma\s?\d[a-z]?(?:-\d+[bB])?|PaLM[- ]?2?)\b',
    "Meta":      r'\b(Llama[- ]?\d(?:\.\d)?(?:[- ]\d+B)?)\b',
    "Anthropic": r'\b(Claude(?:\s?[234](?:\.\d)?)?(?:\s?(?:Opus|Sonnet|Haiku))?)\b',
    "DeepSeek":  r'\b(DeepSeek[- ]?(?:V\d(?:\.\d)?(?:-[\w.]+)?|R\d(?:-[\w.]+)?|LLM|Math(?:-[\w.]+)?|Coder(?:-?V?[\d.]*)?|OCR|VL\d?)[\w.-]*)\b',
    "Qwen":      r'\b(Qwen\d(?:\.\d)?(?:-[\w.]+)?|Qwen-[\w.]+)\b',
    "Zhipu":     r'\b(GLM-?\d+(?:\.\d)?(?:-[\w.]+)*|ChatGLM\d?(?:-[\w.]+)?|CodeGeeX\d?|CogVLM\d?|CogView\d?)\b',
    "Moonshot":  r'\b(Kimi(?:[- ](?:K\d(?:\.\d)?|Linear|Dev|VL|Thinking|Audio)[\w.]*)?)\b',
    "MiniMax":   r'\b(MiniMax[- ](?:M\d(?:\.\d)?|01|VL|Text|Audio|Speech|Video|Agent)[\w.-]*)\b',
    "Xiaomi":    r'\b(MiMo(?:[- ][\w.]+)+|Xiaomi[- ][\w.]+)\b',
    "Tencent":   r'\b(Hunyuan(?:[- ][\w.]+)+|Hunyuan)\b',
    "Microsoft": r'\b(Phi-\d(?:\.\d)?(?:-[\w.]+)*)\b',
    "Nvidia":    r'\b(Nemotron(?:[- ][\w.]+)*)\b',
    "IBM":       r'\b(Granite(?:[- ][\w.]+)*)\b',
    "AllenAI":   r'\b(OLMoE?|OLMo\s?\d(?:\.\d)?|OLMo\s?Hybrid)\b',
    "TII":       r'\b(Falcon(?:[- ](?:H\d[rR]?|\d+|[Mm]amba|[Ee]\d+))?)\b',
    "xAI":       r'\b(Grok[- ]?[\d.]+)\b',
    "01.AI":     r'\b(Yi[- ][\w.]+|Yi)\b',
    "Baichuan":  r'\b(Baichuan[- ][\w.]+|Baichuan\d?)\b',
    "InternLM":  r'\b(InternLM[- ][\w.]+|InternVL[- ][\w.]+|InternVideo[- ]?[\w.]+)\b',
    "Databricks": r'\b(DBRX[\w.-]*)\b',
    "AI21":      r'\b(Jamba[- ]?[\w.]*)\b',
    "LG":        r'\b(EXAONE(?:[- ][\w.]+)*)\b',
    "Mistral":   r'\b(Mistral[- ][\w.]+|Mixtral[- ][\w.]+|Pixtral[- ][\w.]+|Mistral)\b',
    "Baidu":     r'\b(ERNIE[- ][\w.]+|ERNIE)\b',
    "Cohere":    r'\b(Command[- ][\w.+]+|Aya[- ][\w.]+|Aya)\b',
}

# Trailing words that are never part of a model name
TRAILING = re.compile(
    r'(?:\s+(?:Technical|Report|Models?|Series|Family|System|Card|Paper|'
    r'Release|Foundation|Large|Language|Pre-?trained?|Open|Instruct(?:ion)?|'
    r'Tuned|Chat|Context|Pre))+$',
    re.IGNORECASE)

# Tokens that mark the end of a model name when they follow it
STOPWORDS = {'of', 'for', 'to', 'the', 'and', 'with', 'from', 'at', 'in',
             'on', 'a', 'an', 'towards', 'toward', 'via', 'using', 'as'}


def normalize_model(name):
    name = re.sub(r'\s+', ' ', name).strip(' -:.')
    # cut at first connective token ("Mixtral of Experts" -> "Mixtral")
    tokens = name.split(' ')
    for i, t in enumerate(tokens):
        if t.lower().strip('-') in STOPWORDS:
            tokens = tokens[:i]
            break
    name = ' '.join(tokens)
    name = TRAILING.sub('', name).strip(' -:.')
    # unify space/hyphen between family and version: "DeepSeek R1" -> "DeepSeek-R1"
    name = re.sub(r'\s+(?=[\dA-Z])', '-', name)
    return name


def dedupe_key(model):
    """Case/separator-insensitive key so 'DeepSeek-R1' == 'DeepSeek R1'."""
    return re.sub(r'[\s\-.]', '', model).lower()


def extract_model(title, company):
    pat = MODEL_PATTERNS.get(company)
    if not pat:
        return None
    m = re.search(pat, title)
    if not m:
        return None
    model = normalize_model(m.group(1))
    # drop bare family names without version when too generic
    if len(model) < 3:
        return None
    return model


def main():
    cp = json.load(open(os.path.join(TRACKER, "company-papers.json"), encoding="utf-8"))
    notes = {}
    pj = os.path.join(TRACKER, "papers.json")
    if os.path.exists(pj):
        for p in json.load(open(pj, encoding="utf-8")):
            if p.get("note"):
                notes[p["id"]] = p["note"]

    groups = {}
    for p in cp:
        co = p["company"]
        g = groups.setdefault(co, {"company": co, "series": {}, "others": []})
        entry = {"id": p["id"], "title": p["title"], "date": p.get("date", ""),
                 "note": notes.get(p["id"], "")}
        model = extract_model(p["title"], co)
        if model:
            key = dedupe_key(model)
            slot = g["series"].setdefault(key, {"names": {}, "papers": []})
            slot["names"][model] = slot["names"].get(model, 0) + 1
            slot["papers"].append(entry)
        else:
            g["others"].append(entry)

    def display_name(slot):
        # most frequent variant wins; ties -> shortest name
        return sorted(slot["names"].items(),
                      key=lambda kv: (-kv[1], len(kv[0])))[0][0]

    # timeline nodes: one per (company, model), earliest paper is canonical
    models = []
    for co, g in groups.items():
        for key, slot in g["series"].items():
            papers = sorted(slot["papers"], key=lambda x: x.get("date", ""))
            first = papers[0]
            models.append({"model": display_name(slot), "company": co,
                           "date": first.get("date", ""), "id": first["id"],
                           "title": first["title"], "note": first.get("note", ""),
                           "papers": len(papers)})
    models.sort(key=lambda x: x.get("date", ""))

    out_groups = []
    for co in sorted(groups, key=lambda c: -len(groups[c]["series"]) - len(groups[c]["others"]) * 0.01):
        g = groups[co]
        out_groups.append({
            "company": co,
            "series": [{"model": display_name(slot), "papers": slot["papers"]}
                       for key, slot in sorted(
                           g["series"].items(),
                           key=lambda kv: min(p.get("date", "") for p in kv[1]["papers"]))],
            "others": sorted(g["others"], key=lambda x: x.get("date", ""), reverse=True),
        })

    out = {"models": models, "groups": out_groups}
    with open(os.path.join(TRACKER, "models.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"models: {len(models)} releases, {len(out_groups)} companies")
    return out


if __name__ == "__main__":
    main()
