import json

with open("approved_links.json", "r", encoding="utf-8") as f:
    links = json.load(f)

keywords = ["출입문", "psd", "승강장안전문", "판토", "팬터", "비상제동", "atc"]
for l in links:
    source = json.dumps(l["source"], ensure_ascii=False)
    target = json.dumps(l["target"], ensure_ascii=False)
    for kw in keywords:
        if kw in source.lower() or kw in target.lower():
            print(f"Keyword: {kw} | ID: {l['id']} | Relation: {l['relation']}")
            print("  Source:", source[:200])
            print("  Target:", target[:200])
            print("-" * 50)
            break
