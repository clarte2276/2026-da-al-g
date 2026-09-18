import json
from app.db import SessionLocal
from app.models import DocumentContent, Fragment
from sqlalchemy import select

db = SessionLocal()
rule_version = "35315ef6-c82f-44fd-904c-62b78bdc474a"
content = db.get(DocumentContent, rule_version)
text = content.text

articles = [25, 34, 35, 46, 74, 144, 242, 321, 323, 326, 327, 328, 330, 331, 332, 345, 346, 348, 349, 351, 352]
article_texts = {}
for a in articles:
    import re
    m = re.search(rf"(?m)^[ \t]*제{a}조(?:\(|[ \t]|$)", text)
    if m:
        start = m.start()
        m_next = re.search(r"(?m)^[ \t]*제\d+조(?:\(|[ \t]|$)", text[start + 10:])
        end = start + 10 + m_next.start() if m_next else len(text)
        article_texts[f"제{a}조"] = text[start:end].strip()

# Also find PPT fragments for the 5 graph cases
ppt_frags = db.scalars(select(Fragment).where(Fragment.kind.in_(["slide", "pages"]))).all()
print(f"Loaded {len(article_texts)} articles and {len(ppt_frags)} ppt fragments")

with open("article_texts.json", "w", encoding="utf-8") as f:
    json.dump(article_texts, f, ensure_ascii=False, indent=2)

print("Saved article_texts.json")
