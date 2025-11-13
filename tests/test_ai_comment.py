import pytest
from services.session_service import AIService
from models import Gun


@pytest.mark.asyncio
async def test_ai_comment_without_api_key():
    gun = Gun(name="Test Gun", caliber="9mm", user_id="user-1")
    comment = await AIService.generate_comment(gun, distance=25, hits=7, shots=10, accuracy=70.0, api_key=None)
    assert "Brak klucza API OpenAI" in comment


@pytest.mark.asyncio
async def test_ai_comment_with_stub(monkeypatch):
    class DummyResponse:
        class Message:
            content = "Świetna robota!"

        class Choice:
            def __init__(self):
                self.message = DummyResponse.Message()

        def __init__(self):
            self.choices = [DummyResponse.Choice()]

    class DummyClient:
        class Chat:
            class Completions:
                @staticmethod
                def create(*args, **kwargs):
                    return DummyResponse()

            completions = Completions()

        chat = Chat()

    def dummy_openai(api_key: str):
        assert api_key == "test-key"
        return DummyClient()

    monkeypatch.setattr("services.session_service.OpenAI", dummy_openai)

    gun = Gun(name="Stub Gun", caliber="5.56", user_id="user-1")
    comment = await AIService.generate_comment(gun, distance=100, hits=8, shots=10, accuracy=80.0, api_key="test-key")
    assert comment == "Świetna robota!"







