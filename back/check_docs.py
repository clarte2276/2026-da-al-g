from app.db import SessionLocal
from app.models import Document, DocumentVersion, DocumentContent
from sqlalchemy import select

db = SessionLocal()
docs = db.scalars(select(Document)).all()
print(f"Total documents: {len(docs)}")
for d in docs:
    vers = db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == d.id)).all()
    print(f"Doc: ID={d.id} Filename={d.filename} Status={d.status}")
    for v in vers:
        contents = db.scalars(select(DocumentContent).where(DocumentContent.version_id == v.id)).all()
        for c in contents:
            print(f"  Version={v.id} Kind={c.kind} TextLen={len(c.text or '')} Pages={len(c.pages or [])}")
