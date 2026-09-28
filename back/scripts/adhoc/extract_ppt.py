import json
from app.db import SessionLocal
from app.models import Fragment
from sqlalchemy import select

db = SessionLocal()
ppt_versions = ["61b7c6ec-e756-49be-9702-9e4420e0f599", "9fa17af6-51cc-4366-9f1e-d13b4e5b8405"]
fragments = db.scalars(select(Fragment).where(Fragment.version_id.in_(ppt_versions))).all()

# Find slides for:
# 1. door / 전체 열림불능
# 2. psd
# 3. pantograph / 판토그래프
# 4. emergency brake / 비상제동 풀림불능
# 5. atc / ATC 장치 고장
interesting = {}
for f in fragments:
    t = f.text or ""
    page = (f.locator_json or {}).get("page") or (f.locator_json or {}).get("slide")
    for key in ["열림불능", "무선", "판토", "팬터", "비상제동", "atc"]:
        if key in t.lower():
            interesting.setdefault(key, []).append({
                "id": f.id,
                "version_id": f.version_id,
                "page": page,
                "text": t[:400]
            })

with open("interesting_ppt.json", "w", encoding="utf-8") as out:
    json.dump(interesting, out, ensure_ascii=False, indent=2)

print("Saved interesting_ppt.json")
