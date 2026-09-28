import math
import re
from collections import Counter
from app.db import SessionLocal
from app.models import Fragment
from app.services.rag import GraphRAGService, _search_tokens, cosine_similarity
from app.config import get_settings
from app.services.embedding import HashEmbeddingProvider, OpenAIEmbeddingProvider
from sqlalchemy import select

s = get_settings()
provider = OpenAIEmbeddingProvider(s.openai_api_key, s.embedding_model, s.embedding_dimensions) if s.openai_api_key else HashEmbeddingProvider(s.embedding_dimensions)
rag = GraphRAGService(s, provider)
db = SessionLocal()

raw_fragments = db.scalars(select(Fragment).where(Fragment.embedding_json.is_not(None))).all()
article_units = rag._article_units(rag._search_units(db, raw_fragments), db)

# Compute document frequencies for all tokens across article_units
doc_freq = Counter()
N = len(article_units)
unit_tokens_map = {}
for u in article_units:
    tokens = _search_tokens(f"{u.title or ''}\n{u.text or ''}")
    unit_tokens_map[u.id] = tokens
    for t in tokens:
        doc_freq[t] += 1

idf = {t: math.log((N - df + 0.5) / (df + 0.5) + 1.0) for t, df in doc_freq.items()}

cases = [
    ("vehicle_failure", "열차 운전 중 차량고장으로 자력운전이 곤란하면 어떤 조치를 해야 하나요?", "제326조"),
    ("brake_pipe", "정거장 외에서 제동관 또는 공기관 고장으로 통기불능이면 구원과 운전을 어떻게 처리하나요?", "제327조"),
    ("door_failure", "열차 운전 중 출입문 고장이 발생하면 보고, 방송, 응급조치와 회송은 어떻게 하나요?", "제328조"),
    ("rescue_train_protection", "정거장 외에서 사고로 정차한 열차가 구원열차를 요구했을 때 열차방호는 어떻게 하나요?", "제321조"),
    ("adjacent_line_protection", "정거장 외에서 인접 선로를 지장한 경우 어떤 방호와 보고를 해야 하나요?", "제323조"),
    ("automatic_driving", "5~8호선 본선 구간의 운전 방식은 자동운전인가요? 수동운전 예외는 무엇인가요?", "제330조"),
    ("front_cab_failure", "전동차 전부 운전실이 고장 나면 어떤 속도로 어디까지 운전할 수 있나요?", "제331조"),
    ("runaway_vehicle", "유치 중인 차량이 자동으로 굴렀을 때 누구에게 보고하고 어떻게 정차시키나요?", "제332조"),
    ("storm", "열차 운전 중 폭풍을 만나 운전에 위험하다고 판단되면 기관사는 어떻게 해야 하나요?", "제348조"),
    ("flooding", "터널 내 침수로 정전이나 운전 지장이 우려될 때 승무원과 역은 어떻게 조치하나요?", "제349조"),
    ("fog_or_snowstorm", "안개나 눈보라로 신호 확인이 어려울 때 기관사와 운전관제는 어떻게 조치하나요?", "제351조"),
    ("weather_alert", "이상기후 경보의 종류와 열차 운전 규제는 어떻게 정하나요?", "제345조"),
]

for name, q, target_art in cases:
    q_vec = provider.embed([q])[0]
    q_tokens = _search_tokens(q)
    total_q_idf = sum(idf.get(t, 1.0) for t in q_tokens) or 1.0

    scored = []
    for u in article_units:
        v_s = cosine_similarity(q_vec, u.embedding_vector or u.embedding_json or [])
        u_toks = unit_tokens_map[u.id]
        matched_tokens = q_tokens & u_toks
        matched_idf = sum(idf.get(t, 1.0) for t in matched_tokens)
        weighted_overlap = matched_idf / total_q_idf
        score = (v_s * 0.6) + (weighted_overlap * 0.4)
        art = (u.locator_json or {}).get("article")
        scored.append((u, score, art))

    scored.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, item in enumerate(scored) if item[2] == target_art), None)
    top_arts = [item[2] for item in scored[:3]]
    print(f"{name:25s} Target: {target_art} -> Rank: {rank} (Top 3: {top_arts})")
