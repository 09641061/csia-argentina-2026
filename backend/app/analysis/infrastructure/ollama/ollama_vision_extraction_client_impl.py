from __future__ import annotations

import base64
import json
from pathlib import Path

from app.analysis.application.internal.outboundservices.ollama_vision_extraction_client import (
    OllamaVisionExtractionClient,
)
from app.analysis.domain.exceptions import (
    AnalysisModelInvalidResponseError,
    AnalysisModelTimeoutError,
    AnalysisModelUnavailableError,
)
from app.analysis.domain.model.valueobjects.vision_extraction_result import (
    VisionExtractionResult,
)
from app.shared.infrastructure.ollama.ollama_chat_transport import (
    OllamaChatTransport,
    OllamaMalformedResponseError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)

_REQUIRED_FIELDS = {"visible_text", "visual_summary", "document_type"}


class OllamaVisionExtractionClientImpl(OllamaVisionExtractionClient):
    """Mandatory local-AI extraction for uploaded images."""

    def __init__(
        self,
        *,
        base_url: str,
        model_name: str,
        request_timeout_seconds: int,
        context_tokens: int,
        max_output_tokens: int,
    ) -> None:
        if not model_name.strip():
            raise ValueError("Ollama vision model name is required")
        if min(request_timeout_seconds, context_tokens, max_output_tokens) <= 0:
            raise ValueError("Ollama vision numeric settings must be positive")
        self._transport = OllamaChatTransport(base_url)
        self._model_name = model_name
        self._request_timeout_seconds = request_timeout_seconds
        self._context_tokens = context_tokens
        self._max_output_tokens = max_output_tokens
        self._system_prompt = self._load_system_prompt()

    @property
    def model_name(self) -> str:
        return self._model_name

    async def extract(
        self,
        *,
        image_content: bytes,
        mime_type: str,
        reference_label: str,
    ) -> VisionExtractionResult:
        del mime_type
        # The filename is never shown to the model. It is chosen by the uploader,
        # it describes nothing that the pixels do not already show, and a suggestive
        # name measurably drags the transcription towards what the name claims.
        del reference_label
        if not image_content:
            raise AnalysisModelInvalidResponseError("The image is empty")
        encoded_image = base64.b64encode(image_content).decode("ascii")
        try:
            raw_content = await self._transport.chat(
                model_name=self._model_name,
                system_prompt=self._system_prompt,
                user_prompt=(
                    "Transcribe and describe the attached image. visible_text must be one "
                    "complete string preserving every readable line, including emails, "
                    "identifiers, numbers and punctuation, and must be an empty string when "
                    "the image contains no readable text. visual_summary must always describe "
                    "what the image shows. Return exactly the required JSON."
                ),
                timeout_seconds=self._request_timeout_seconds,
                options={
                    "num_ctx": self._context_tokens,
                    "num_predict": self._max_output_tokens,
                    "temperature": 0,
                },
                json_format=True,
                images=[encoded_image],
            )
        except OllamaTimeoutError as error:
            raise AnalysisModelTimeoutError(
                f"Ollama vision model {self._model_name} exceeded its timeout"
            ) from error
        except (OllamaUnavailableError, OSError) as error:
            raise AnalysisModelUnavailableError(
                f"Unable to reach Ollama vision model {self._model_name}"
            ) from error
        except OllamaMalformedResponseError as error:
            raise AnalysisModelInvalidResponseError(
                "The local vision model returned a malformed response"
            ) from error

        try:
            payload = json.loads(raw_content)
        except json.JSONDecodeError as error:
            raise AnalysisModelInvalidResponseError(
                "The local vision model did not return valid JSON"
            ) from error
        if not isinstance(payload, dict) or set(payload) != _REQUIRED_FIELDS:
            raise AnalysisModelInvalidResponseError(
                "The local vision model returned an invalid extraction contract"
            )
        if any(not isinstance(payload[field], str) for field in _REQUIRED_FIELDS):
            raise AnalysisModelInvalidResponseError(
                "The local vision extraction fields must be strings"
            )
        try:
            return VisionExtractionResult(
                visible_text=payload["visible_text"],
                visual_summary=payload["visual_summary"],
                document_type=payload["document_type"],
                model_name=self._model_name,
            )
        except ValueError as error:
            raise AnalysisModelInvalidResponseError(
                "The local vision model returned unusable extracted content"
            ) from error

    def _load_system_prompt(self) -> str:
        prompt_path = (
            Path(__file__).resolve().parents[3]
            / "shared"
            / "prompts"
            / "vision_extraction_system_prompt.md"
        )
        return prompt_path.read_text(encoding="utf-8").strip()
