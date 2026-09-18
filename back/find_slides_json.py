import json

with open("interesting_ppt.json", "r", encoding="utf-8") as f:
    data = json.load(f)

matches = []
seen = set()
for key, items in data.items():
    for it in items:
        t = it["text"]
        for target in ["출입문 전체", "전체 열림", "판토그래프 상승불능", "팬터 상승불능", "비상제동 풀림불능", "비상제동 완해불능", "atc 장치 고장", "atc 고장"]:
            if target in t.lower():
                k = (it["version_id"], it["page"])
                if k not in seen:
                    seen.add(k)
                    matches.append({
                        "target": target,
                        "version_id": it["version_id"],
                        "page": it["page"],
                        "text": t
                    })
                break

with open("graph_slide_matches.json", "w", encoding="utf-8") as f:
    json.dump(matches, f, ensure_ascii=False, indent=2)

print(f"Saved {len(matches)} slide matches")
