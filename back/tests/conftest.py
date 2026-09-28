import pytest


@pytest.fixture(autouse=True)
def _no_real_openai(monkeypatch):
    """Settings() reads the developer's .env; keep tests off the real OpenAI API."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
