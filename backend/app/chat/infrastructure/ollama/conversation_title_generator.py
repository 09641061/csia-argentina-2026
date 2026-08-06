from pathlib import Path

from app.shared.infrastructure.ollama.ollama_chat_transport import OllamaChatTransport


class ConversationTitleGenerator:
    def __init__(self, base_url: str, model_name: str, timeout_seconds: int) -> None:
        self._transport = OllamaChatTransport(base_url)
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        prompt_path = (
            Path(__file__).resolve().parents[3]
            / "shared"
            / "prompts"
            / "conversation_title_system_prompt.md"
        )
        self._system_prompt = prompt_path.read_text(encoding="utf-8").strip()

    async def generate(self, first_message: str) -> str:
        title = await self._transport.chat(
            model_name=self._model_name,
            system_prompt=self._system_prompt,
            user_prompt=first_message.strip(),
            timeout_seconds=self._timeout_seconds,
            options={"num_ctx": 2048, "num_predict": 24, "temperature": 0.1},
            json_format=False,
        )
        normalized = " ".join(title.split()).strip(" \"'`.,:;-")
        if not normalized:
            raise ValueError("The title model returned an empty title")
        return normalized[:160]
