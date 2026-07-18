'''Tencent MaaS TokenHub HTTP gateway.'''
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


class TencentMaaSError(RuntimeError):
    '''A safe provider error that does not expose credentials or resume text.'''

    def __init__(
        self,
        message: str,
        *,
        model_fallback_allowed: bool = False,
        status_code: int | None = None,
        provider_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.model_fallback_allowed = model_fallback_allowed
        self.status_code = status_code
        self.provider_code = provider_code


@dataclass(slots=True)
class TextGenerationResult:
    content: str
    usage: dict[str, int]
    model_name: str | None = None


QUOTA_OR_RATE_LIMIT_CODES = {'401007', '401008', '20097'}
MODELS_WITHOUT_JSON_RESPONSE_FORMAT = {'glm-5', 'minimax-m2.7', 'minimax-m2.5'}


class TencentMaaSModelGateway:
    def __init__(self) -> None:
        self.base_url = settings.TENCENT_MAAS_BASE_URL.rstrip('/')
        self.api_key = settings.TENCENT_MAAS_API_KEY.strip()
        self.timeout = settings.AI_REQUEST_TIMEOUT_SECONDS

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise TencentMaaSError('未配置腾讯云 MaaS API Key')
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model_name: str | None = None,
        max_tokens: int | None = None,
    ) -> TextGenerationResult:
        output_tokens = max(1, min(max_tokens or settings.AI_MAX_OUTPUT_TOKENS, settings.AI_MAX_OUTPUT_TOKENS))
        candidates = self._model_candidates(model_name or settings.RESUME_OPTIMIZATION_MODEL)
        exhausted_models: list[str] = []
        for candidate in candidates:
            payload = {
                'model': candidate,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                'temperature': settings.AI_TEMPERATURE,
                'max_tokens': output_tokens,
                'stream': False,
                'enable_thinking': settings.AI_THINKING_ENABLED,
            }
            if candidate not in MODELS_WITHOUT_JSON_RESPONSE_FORMAT:
                payload['response_format'] = {'type': 'json_object'}
            try:
                data = await self._post_json('/chat/completions', payload)
            except TencentMaaSError as exc:
                if exc.model_fallback_allowed:
                    exhausted_models.append(candidate)
                    continue
                raise
            try:
                choice = data['choices'][0]
                content = choice['message']['content']
            except (KeyError, IndexError, TypeError) as exc:
                raise TencentMaaSError('腾讯云模型返回结构不完整') from exc
            if not isinstance(content, str) or not content.strip():
                raise TencentMaaSError('腾讯云模型返回了空内容')
            finish_reason = choice.get('finish_reason')
            if finish_reason in {'length', 'max_tokens'}:
                raise TencentMaaSError('腾讯云模型输出过长被截断，请减少简历内容或提高 AI_MAX_OUTPUT_TOKENS')
            raw_usage = data.get('usage') or {}
            usage = {
                'prompt_tokens': int(raw_usage.get('prompt_tokens') or 0),
                'completion_tokens': int(raw_usage.get('completion_tokens') or 0),
                'total_tokens': int(raw_usage.get('total_tokens') or 0),
            }
            return TextGenerationResult(content=content, usage=usage, model_name=candidate)

        if exhausted_models:
            raise TencentMaaSError(
                '所有配置模型的额度均已用尽或当前被限流，请稍后重试',
                model_fallback_allowed=True,
            )
        raise TencentMaaSError('没有可用的腾讯云文本模型配置')

    @staticmethod
    def _model_candidates(primary_model: str) -> list[str]:
        configured = settings.tencent_maas_chat_model_list
        if primary_model in configured:
            return configured[configured.index(primary_model):]
        return list(dict.fromkeys([primary_model, *configured]))

    async def embed_text(self, text: str) -> list[float]:
        safe_text = text.strip()
        if not safe_text:
            raise TencentMaaSError('不能为文本空内容生成向量')
        payload = {
            'model': settings.TENCENT_MAAS_EMBEDDING_MODEL,
            'input': [{'type': 'text', 'text': safe_text}],
        }
        data = await self._post_json(settings.TENCENT_MAAS_EMBEDDING_ENDPOINT, payload)
        embedding = self._extract_embedding(data)
        if len(embedding) != settings.TENCENT_MAAS_EMBEDDING_DIMENSION:
            raise TencentMaaSError('Embedding 返回维度与配置不一致')
        return embedding

    @staticmethod
    def _extract_embedding(data: dict[str, Any]) -> list[float]:
        raw = data.get('data')
        candidate: Any = None
        if isinstance(raw, list) and raw:
            candidate = raw[0].get('embedding') if isinstance(raw[0], dict) else None
        elif isinstance(raw, dict):
            candidate = raw.get('embedding')
        if candidate is None and isinstance(data.get('embedding'), list):
            candidate = data['embedding']
        if not isinstance(candidate, list) or not candidate:
            raise TencentMaaSError('Embedding 接口返回结构不完整')
        try:
            return [float(value) for value in candidate]
        except (TypeError, ValueError) as exc:
            raise TencentMaaSError('Embedding 接口返回了非法向量') from exc

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        attempts = max(1, settings.AI_MAX_RETRIES + 1)
        last_error: Exception | None = None
        url = f'{self.base_url}/{path.lstrip("/")}'
        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=self._headers(), json=payload)
                if response.status_code >= 400:
                    provider_code = self._provider_error_code(response)
                    if response.status_code in (401, 403):
                        raise TencentMaaSError('腾讯云模型鉴权失败，请检查 API Key')
                    if (
                        response.status_code in (402, 429)
                        or provider_code in QUOTA_OR_RATE_LIMIT_CODES
                    ):
                        raise TencentMaaSError(
                            '当前腾讯云模型额度已用尽或被限流，正在尝试备用模型',
                            model_fallback_allowed=True,
                            status_code=response.status_code,
                            provider_code=provider_code,
                        )
                    raise TencentMaaSError(
                        f'腾讯云模型请求失败，状态码 {response.status_code}',
                        status_code=response.status_code,
                        provider_code=provider_code,
                    )
                body = response.json()
                if not isinstance(body, dict):
                    raise TencentMaaSError('腾讯云模型返回了非法 JSON')
                return body
            except TencentMaaSError:
                raise
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    await asyncio.sleep(min(2 ** attempt, 4))
        raise TencentMaaSError('腾讯云模型网络请求失败') from last_error

    @staticmethod
    def _provider_error_code(response: httpx.Response) -> str | None:
        try:
            body = response.json()
        except ValueError:
            return None
        error = body.get('error') if isinstance(body, dict) else None
        if not isinstance(error, dict):
            return None
        code = error.get('code')
        return str(code).strip() if code is not None else None
