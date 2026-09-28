import json

with open("interesting_ppt.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for key, items in data.items():
    for it in items:
        t = it["text"]
        for target in ["출입문 전체", "전체 열림", "판토그래프 상승불능", "팬터 상승불능", "비상제동 풀림불능", "비상제동 완해불능", "atc 장치 고장", "atc 고장"]:
            if target in t.lower():
                print(f"Target: {target} | Version: {it['version_id']} | Page: {it['page']}")
                print(t[:300].replace("\n", " "))
                print("=" * 60)
                break
