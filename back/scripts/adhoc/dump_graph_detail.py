import json
from app.db import SessionLocal
from app.models import Fragment, DocumentContent
from sqlalchemy import select

db = SessionLocal()

# PPT slides to dump
targets = [
    ("guide_door", "61b7c6ec-e756-49be-9702-9e4420e0f599", [47, 48, 49, 50]),
    ("guide_psd", "61b7c6ec-e756-49be-9702-9e4420e0f599", [28, 29]),
    ("guide_pantograph", "61b7c6ec-e756-49be-9702-9e4420e0f599", [35, 36]),
    ("guide_emergency_brake", "9fa17af6-51cc-4366-9f1e-d13b4e5b8405", [2, 3, 4, 5, 6, 7]),
    ("guide_atc", "9fa17af6-51cc-4366-9f1e-d13b4e5b8405", [46, 47]),
]

res = {}
for case_name, v_id, pages in targets:
    frags = db.scalars(select(Fragment).where(
        Fragment.version_id == v_id,
        Fragment.kind.in_(["slide", "pages"])
    )).all()
    case_slides = []
    for p in pages:
        for f in frags:
            page = (f.locator_json or {}).get("page") or (f.locator_json or {}).get("slide")
            if page == p:
                case_slides.append({
                    "page": p,
                    "text": f.text or ""
                })
    res[case_name] = case_slides

with open("graph_cases_detail.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)

print("Saved graph_cases_detail.json")
