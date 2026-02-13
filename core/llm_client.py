import requests

class LLMClient:
    def __init__(self):
        # configure your default model / endpoint here
        self.default_model = "gpt-4"
        self.base_url = "http://localhost:8000/chat"  # example
        self.api_key = ""  # if needed

    def chat(self, messages, model: str | None = None) -> str:
        model = model or self.default_model
        # messages: list[{"role": "user"/"assistant"/"system", "content": "..."}]

        resp = requests.post(
            self.base_url,
            json={"model": model, "messages": messages},
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        # adapt to your API schema:
        return data["choices"][0]["message"]["content"]
