import json
from app.db import SessionLocal
from app.models import DocumentContent, Fragment
from sqlalchemy import select

db = SessionLocal()
rule_version = "35315ef6-c82f-44fd-904c-62b78bdc474a"
rule_content = db.get(DocumentContent, rule_version).text

ppt1_version = "61b7c6ec-e756-49be-9702-9e4420e0f599" # 6호선 응급조치 가이드-1
ppt2_version = "9fa17af6-51cc-4366-9f1e-d13b4e5b8405" # 6호선 응급조치 가이드-2

# Let's extract clean references for each case directly from the regulation and PPT source texts!
print("Extracting references for 17 cases...")
