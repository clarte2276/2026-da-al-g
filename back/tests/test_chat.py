import json
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AuditEvent, Base, Fragment
from app.services.chat import ChatResult, ChatService
from app.services.rag import ANSWER_FOCUS_REMINDER, Evidence


class _FailingRag:
    def retrieve(self, *args, **kwargs):
        raise AssertionError("general conversation must not search documents")


class _FakeCompletions:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.responses)


class _FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=_FakeCompletions(responses))


def _message(content="", tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


def test_greeting_skips_rag(tmp_path):
    service = ChatService(
        Settings(storage_root=tmp_path, openai_api_key=None),
        _FailingRag(),
    )

    result = service.respond(None, "안녕", [])

    assert result.mode == "general"
    assert result.evidence == []


def test_preview_search_never_generates_an_answer(monkeypatch):
    from app import main
    from app.schemas import RAGQuery

    class _Rag:
        calls = 0

        def retrieve(self, *args, **kwargs):
            self.calls += 1
            return []

        def answer(self, *args, **kwargs):
            raise AssertionError("preview must not generate an answer")

    rag = _Rag()
    monkeypatch.setattr(main, "rag_service", rag)

    preview = main.rag_query(RAGQuery(question="열차 고장 조치", preview_only=True), None, None)
    general = main.rag_query(RAGQuery(question="오늘 날씨", preview_only=True), None, None)

    assert preview.answer == general.answer == ""
    assert rag.calls == 1


def test_general_llm_response_skips_rag_and_keeps_history(tmp_path):
    client = _FakeClient([SimpleNamespace(choices=[SimpleNamespace(message=_message("반가워요."))])])
    service = ChatService(
        Settings(storage_root=tmp_path, openai_api_key="test"),
        _FailingRag(),
        client,
    )

    result = service.respond(
        None,
        "오늘 기분이 좋아",
        [{"role": "user", "content": "안녕하세요"}],
    )

    assert result.mode == "general"
    assert result.answer == "반가워요."
    assert client.chat.completions.calls[0]["messages"][-2:] == [
        {"role": "user", "content": "안녕하세요"},
        {"role": "user", "content": "오늘 기분이 좋아"},
    ]


def test_document_tool_result_is_grounded(tmp_path):
    call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(
            name="search_documents",
            arguments='{"query":"차량 고장 조치"}',
        ),
    )
    evidence = Evidence(
        fragment=SimpleNamespace(
            id="fragment-1",
            text="차량 고장 시 관제에 보고합니다.",
            title="운전 규정",
            locator_json={"page": 3},
        ),
        score=0.9,
        hop=0,
        path=["fragment-1"],
        filename="운전 규정.hwp",
    )

    class _Rag:
        def retrieve(self, *args, **kwargs):
            return [evidence]

    client = _FakeClient(
        [
            SimpleNamespace(choices=[SimpleNamespace(message=_message(tool_calls=[call]))]),
            SimpleNamespace(choices=[SimpleNamespace(message=_message("관제에 보고합니다. [근거 1]"))]),
        ]
    )
    service = ChatService(
        Settings(storage_root=tmp_path, openai_api_key="test"),
        _Rag(),
        client,
    )

    result = service.respond(None, "차량 고장 시 어떻게 하나요?", [])

    assert result.mode == "rag"
    assert result.evidence == [evidence]
    assert len(client.chat.completions.calls) == 2
    # 근거 뒤에 답변 초점과 노선·상황별 특칙을 함께 지시한다.
    final_messages = client.chat.completions.calls[1]["messages"]
    assert final_messages[-2] == {
        "role": "system",
        "content": ANSWER_FOCUS_REMINDER,
    }
    assert final_messages[-1]["role"] == "system"
    assert "5~8호선 특칙" in final_messages[-1]["content"]
    assert "반드시 답변에 포함" in final_messages[-1]["content"]


def test_answer_log_preserves_synthetic_article_evidence():
    from app.main import _log_answer

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    text = "제25조(휴가) 가족돌봄휴가를 사용할 수 있다. " * 100
    evidence = Evidence(
        fragment=Fragment(id="v1:article:25:0", title="취업규칙 제25조", text=text),
        score=0.91234,
        hop=0,
        path=["v1:article:25:0"],
        filename="취업규칙.hwp",
        location="제25조",
        version_id="v1",
        page=3,
    )

    with Session(engine) as db:
        _log_answer(db, "u1", "휴가 질문", ChatResult("휴가 답변", "rag", [evidence]))
        assert db.get(Fragment, evidence.fragment.id) is None
        event = db.scalar(select(AuditEvent).where(AuditEvent.action == "chat.answer"))
        assert event.payload_json["evidence"] == [{
            "fragment_id": "v1:article:25:0",
            "title": "취업규칙 제25조",
            "text": text[:2000],
            "link_id": None,
            "filename": "취업규칙.hwp",
            "location": "제25조",
            "version_id": "v1",
            "page": 3,
            "score": 0.9123,
            "hop": 0,
        }]


@pytest.mark.parametrize("question", [
    "한 달에 휴가는 몇 번 쓸 수 있어",
    "휴직", "연차", "수당", "급여", "근무", "복무", "징계", "승진", "교육", "출장",
])
def test_hr_questions_search_documents_offline(tmp_path, question):
    evidence = Evidence(fragment=Fragment(id="leave", text="휴가 규정"), score=1.0, hop=0, path=[])

    class _Rag:
        def retrieve(self, db, query, **kwargs):
            assert query == question
            return [evidence]

        def answer(self, query, found):
            assert query == question
            assert found == [evidence]
            return "휴가 규정 답변"

    service = ChatService(Settings(storage_root=tmp_path, openai_api_key=None), _Rag())

    assert service._looks_like_document_question(question)
    result = service.respond(None, question, [])
    assert result.mode == "rag"
    assert result.evidence == [evidence]
    assert result.answer == "휴가 규정 답변"


def test_hr_questions_require_search_tool_online(tmp_path):
    question = "한 달에 휴가는 몇 번 쓸 수 있어"
    call = SimpleNamespace(
        id="leave-call",
        function=SimpleNamespace(name="search_documents", arguments='{"query":"취업규칙 휴가 사용 횟수"}'),
    )

    class _Rag:
        def retrieve(self, db, query, **kwargs):
            assert question in query
            assert "취업규칙 휴가 사용 횟수" in query
            return []

    client = _FakeClient([SimpleNamespace(choices=[SimpleNamespace(message=_message(tool_calls=[call]))])])
    service = ChatService(Settings(storage_root=tmp_path, openai_api_key="test"), _Rag(), client)

    result = service.respond(None, question, [])

    assert result.mode == "insufficient_evidence"
    request = client.chat.completions.calls[0]
    assert request["tool_choice"] == {"type": "function", "function": {"name": "search_documents"}}
    prompt = request["messages"][0]["content"]
    description = request["tools"][0]["function"]["description"]
    for rewrite in ("급정거→급정차·정차 시 조치", "긴급상황→이례상황·사고 발생 시 조치", "자동문→출입문 고장"):
        assert rewrite in prompt
        assert rewrite in description
    assert "꼭 필요하면 유지" in prompt
    assert "only when it is not essential" in description


def test_linked_evidence_does_not_displace_search_hits():
    def item(hop):
        return Evidence(fragment=Fragment(id=str(hop)), score=0.0, hop=hop, path=[])

    limited = ChatService._limit_evidence([item(1), item(1), *[item(0) for _ in range(6)]], 5)

    assert [e.hop for e in limited] == [0, 0, 0, 0, 0, 1, 1]


def test_linked_evidence_is_capped():
    def item(hop):
        return Evidence(fragment=Fragment(id=str(hop)), score=0.0, hop=hop, path=[])

    limited = ChatService._limit_evidence([item(0), *[item(1) for _ in range(5)]], 5)

    assert [e.hop for e in limited] == [0, 1, 1, 1]


def test_linked_evidence_names_the_passage_it_came_from():
    seed = Evidence(fragment=Fragment(id="slide-28", text="PSD"), score=1.0, hop=0, path=["slide-28"])
    linked = Evidence(fragment=Fragment(id="link:x", text="제46조"), score=0.9, hop=1, path=["slide-28", "link-1"])

    items = json.loads(ChatService._evidence_json([seed, linked]))["evidence"]

    assert [item["cite_as"] for item in items] == ["[근거 1]", "[근거 2]"]
    assert items[0]["linked_from"] is None
    assert items[1]["linked_from"].startswith("근거 1의")
    assert items[1]["text"].startswith("[근거 2]")


def test_stream_yields_progress_deltas_then_cleaned_result(tmp_path):
    call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="search_documents", arguments='{"query":"q"}'),
    )
    evidence = Evidence(
        fragment=SimpleNamespace(id="f1", text="관제에 보고", title="규정", locator_json={}),
        score=0.9,
        hop=0,
        path=["f1"],
        filename="규정.hwp",
    )

    class _Rag:
        def retrieve(self, *args, **kwargs):
            return [evidence]

    def chunk(text):
        return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])

    client = _FakeClient(
        [
            SimpleNamespace(choices=[SimpleNamespace(message=_message(tool_calls=[call]))]),
            iter([chunk("관제에 "), chunk(None), chunk("보고합니다. [근거 9]")]),
        ]
    )
    service = ChatService(Settings(storage_root=tmp_path, openai_api_key="test"), _Rag(), client)

    events = list(service.respond_stream(None, "차량 고장 시 어떻게 하나요?", []))

    assert [e for e in events if isinstance(e, tuple) and e[0] == "delta"] == [
        ("delta", "관제에 "),
        ("delta", "보고합니다. [근거 9]"),
    ]
    assert ("status", "규정을 찾는 중") in events
    result = events[-1]
    assert result.mode == "rag"
    assert "[근거 9]" not in result.answer  # 없는 근거 번호는 최종 답변에서 정리된다
    assert client.chat.completions.calls[1]["stream"] is True
