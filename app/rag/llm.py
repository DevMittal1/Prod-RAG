import asyncio
from typing import Protocol

from google import genai
from google.genai import types

from app.core.config import Settings
from app.schemas.common import RetrievedChunk


class LLMGateway(Protocol):
    async def generate(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        conversation: list[dict[str, str]],
    ) -> str:
        ...


class GeminiLLMGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    async def generate(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        conversation: list[dict[str, str]],
    ) -> str:
        if not self.client:
            return _fallback_answer(query, chunks)

        context = "\n\n".join(f"Source {idx + 1}: {chunk.text}" for idx, chunk in enumerate(chunks))
        history = "\n".join(
            f"{turn['role']}: {turn['content']}" for turn in conversation[-6:]
        )
        prompt = (
            f"Recent conversation:\n{history or 'None'}\n\n"
            f"Question: {query}\n\n"
            f"Context:\n{context}"
        )
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=(
                    "Answer using only the supplied context. Cite source numbers when useful. "
                    "If the answer is not in context, say you do not know."
                ),
            ),
        )
        return response.text or ""


def _fallback_answer(query: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "I do not know based on the available context."
    return f"Offline answer for '{query}'. Most relevant context: {chunks[0].text[:500]}"
