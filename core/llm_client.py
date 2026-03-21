# core/llm_client.py

import os
from typing import List, Dict, Optional

from dotenv import load_dotenv
import google.genai as genai


# Load environment variables from .env at project root
load_dotenv()


class LLMClient:
    """
    LLM client using the new google.genai SDK (Gemini API).

    Expects messages in the form:
        [{"role": "user" | "assistant" | "system", "content": "text"}, ...]
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env or environment")

        # Create a client
        self.client = genai.Client(api_key=api_key)

        # Pick a model that exists for your key. Adjust if needed.
        # Common small / cheap model:
        self.default_model = "gemini-2.5-flash"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> str:
        """
        Send a chat history to Gemini and return the assistant reply as text.

        For simplicity, we flatten the history into a single text prompt.
        """
        model_name = model or self.default_model

        # Build a single prompt from the full history
        parts = []
        for m in messages:
            role = m.get("role", "user")
            text = m.get("content", "")
            if not text:
                continue

            if role == "system":
                prefix = "System:"
            elif role == "assistant":
                prefix = "Assistant:"
            else:
                prefix = "User:"

            parts.append(f"{prefix} {text}")

        prompt = "\n".join(parts) or "You are a helpful assistant."

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            # google.genai response has .text
            return response.text or ""
        except Exception as e:
            print("LLMClient / google.genai error:", repr(e))
            return "I could not reach the AI service right now."
