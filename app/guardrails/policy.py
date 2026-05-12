from fastapi import HTTPException


class GuardrailService:
    blocked_terms = {"ignore previous instructions", "reveal system prompt"}

    def validate_input(self, text: str) -> None:
        normalized = text.lower()
        if any(term in normalized for term in self.blocked_terms):
            raise HTTPException(status_code=400, detail="Query violates safety policy")

    def validate_output(self, text: str) -> None:
        if not text.strip():
            raise HTTPException(status_code=502, detail="Model returned an empty response")

