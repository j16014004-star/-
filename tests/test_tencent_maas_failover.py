import pytest

from app.ai.tencent_maas import TencentMaaSError, TencentMaaSModelGateway
from app.core.config import settings


MODEL_CHAIN = (
    "deepseek-v4-flash,glm-5.1,minimax-m2.7,minimax-m2.5,glm-5,kimi-k2.5"
)


def _success_payload(content: str = '{"ok": true}') -> dict:
    return {
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


@pytest.mark.asyncio
async def test_quota_exhaustion_switches_to_next_model_in_configured_order(monkeypatch):
    monkeypatch.setattr(settings, "TENCENT_MAAS_CHAT_MODELS", MODEL_CHAIN)
    gateway = TencentMaaSModelGateway()
    called_models: list[str] = []

    async def fake_post(_path, payload):
        called_models.append(payload["model"])
        if payload["model"] in {"deepseek-v4-flash", "glm-5.1"}:
            raise TencentMaaSError(
                "quota exhausted", model_fallback_allowed=True, provider_code="20097"
            )
        return _success_payload()

    monkeypatch.setattr(gateway, "_post_json", fake_post)
    result = await gateway.generate_json(system_prompt="system", user_prompt="user")

    assert called_models == ["deepseek-v4-flash", "glm-5.1", "minimax-m2.7"]
    assert result.model_name == "minimax-m2.7"
    assert result.usage["total_tokens"] == 15


@pytest.mark.asyncio
async def test_authentication_error_does_not_switch_model(monkeypatch):
    monkeypatch.setattr(settings, "TENCENT_MAAS_CHAT_MODELS", MODEL_CHAIN)
    gateway = TencentMaaSModelGateway()
    called_models: list[str] = []

    async def fake_post(_path, payload):
        called_models.append(payload["model"])
        raise TencentMaaSError("invalid api key")

    monkeypatch.setattr(gateway, "_post_json", fake_post)
    with pytest.raises(TencentMaaSError, match="invalid api key"):
        await gateway.generate_json(system_prompt="system", user_prompt="user")

    assert called_models == ["deepseek-v4-flash"]


@pytest.mark.asyncio
async def test_models_without_structured_output_omit_response_format(monkeypatch):
    monkeypatch.setattr(settings, "TENCENT_MAAS_CHAT_MODELS", MODEL_CHAIN)
    gateway = TencentMaaSModelGateway()
    captured: dict = {}

    async def fake_post(_path, payload):
        captured.update(payload)
        return _success_payload()

    monkeypatch.setattr(gateway, "_post_json", fake_post)
    result = await gateway.generate_json(
        system_prompt="system", user_prompt="user", model_name="minimax-m2.5"
    )

    assert result.model_name == "minimax-m2.5"
    assert "response_format" not in captured


def test_provider_quota_error_code_is_read_as_string():
    class FakeResponse:
        @staticmethod
        def json():
            return {"error": {"code": 20097}}

    assert TencentMaaSModelGateway._provider_error_code(FakeResponse()) == "20097"
