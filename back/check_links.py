from app.db import SessionLocal
from app.models import DocumentLink, Document, DocumentVersion
from sqlalchemy import select

db = SessionLocal()
links = db.scalars(select(DocumentLink)).all()
print(f"Total DocumentLinks: {len(links)}")
for l in links:
    print(f"Link: ID={l.id} Relation={l.relation_type} Status={l.status}")
    print(f"  Source: {l.source_selection}")
    print(f"  Target: {l.target_selection}")
