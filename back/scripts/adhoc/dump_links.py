import json
from app.db import SessionLocal
from app.models import DocumentLink
from sqlalchemy import select

db = SessionLocal()
links = db.scalars(select(DocumentLink).where(DocumentLink.status == "approved")).all()
output = []
for l in links:
    output.append({
        "id": l.id,
        "relation": l.relation_type,
        "source": l.source_selection,
        "target": l.target_selection,
    })

with open("approved_links.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(output)} approved links to approved_links.json")
