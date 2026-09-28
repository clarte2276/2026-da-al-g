from app.db import SessionLocal
from app.models import DocumentContent

db = SessionLocal()
rule_version = "35315ef6-c82f-44fd-904c-62b78bdc474a"
text = db.get(DocumentContent, rule_version).text

for num in [305, 315, 321]:
    import re
    m = re.search(rf"(?m)^[ \t]*제{num}조(?:\(|[ \t]|$)", text)
    if m:
        start = m.start()
        m_next = re.search(r"(?m)^[ \t]*제\d+조(?:\(|[ \t]|$)", text[start + 10:])
        end = start + 10 + m_next.start() if m_next else len(text)
        print(f"--- 제{num}조 ---")
        print(text[start:end].strip()[:300])
