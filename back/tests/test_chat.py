from types import SimpleNamespace

from app.config import Settings
from app.services.chat import ChatService
from app.services.rag import Evidence


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
