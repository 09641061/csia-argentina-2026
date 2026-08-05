from __future__ import annotations

import asyncio
import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaTransportError(RuntimeError):
    pass


class OllamaTimeoutError(OllamaTransportError):
    pass


class OllamaUnavailableError(OllamaTransportError):
    pass


class OllamaMalformedResponseError(OllamaTransportError):
    pass


class OllamaChatTransport:
    """
    Minimal HTTP transport for the local Ollama chat endpoint.

    It carries no prompt and no policy of its own: the security evaluator and
    the answer generator each build their own system prompt, options and
    response contract on top of it, so the two responsibilities cannot leak into
    one another.
    """

    def __init__(self, base_url: str) -> None:
        if not base_url.strip():
            raise ValueError("Ollama base URL is required")
        self._base_url = base_url.rstrip("/")

    @property
    def base_url(self) -> str:
        return self._base_url

    async def chat(
        self,
        *,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: int,
        options: dict[str, object],
        json_format: bool,
        images: list[str] | None = None,
    ) -> str:
        return await asyncio.to_thread(
            self._chat,
            model_name,
            system_prompt,
            user_prompt,
            timeout_seconds,
            options,
            json_format,
            images,
        )

    def _chat(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: int,
        options: dict[str, object],
        json_format: bool,
        images: list[str] | None,
    ) -> str:
        user_message: dict[str, object] = {"role": "user", "content": user_prompt}
        if images:
            user_message["images"] = images
        payload: dict[str, object] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                user_message,
            ],
            "stream": False,
            "options": options,
        }
        if json_format:
            payload["format"] = "json"

        request = Request(
            url=f"{self._base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                body = response.read()
        except TimeoutError as error:
            raise OllamaTimeoutError(f"Ollama model {model_name} exceeded its timeout") from error
        except HTTPError as error:
            raise OllamaUnavailableError(
                f"Ollama model {model_name} returned HTTP {error.code}"
            ) from error
        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise OllamaTimeoutError(
                    f"Ollama model {model_name} exceeded its timeout"
                ) from error
            raise OllamaUnavailableError(f"Unable to reach Ollama at {self._base_url}") from error
        except OSError as error:
            raise OllamaUnavailableError(f"Unable to reach Ollama at {self._base_url}") from error

        try:
            envelope = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise OllamaMalformedResponseError("Ollama returned a malformed envelope") from error

        if not isinstance(envelope, dict):
            raise OllamaMalformedResponseError("Ollama envelope is not an object")
        message = envelope.get("message")
        if not isinstance(message, dict) or "content" not in message:
            raise OllamaMalformedResponseError("Ollama envelope has no message content")
        content = message["content"]
        if not isinstance(content, str):
            raise OllamaMalformedResponseError("Ollama message content is not text")
        return content
