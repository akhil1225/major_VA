import json
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


@dataclass
class AIMessage:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class AIChat:
    id: str
    title: str
    messages: List[AIMessage]


class AIChatStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.file = self.base_dir / "ai_chats.json"
        self.chats: List[AIChat] = []
        self.load()

    def load(self):
        if not self.file.exists():
            self.chats = []
            return
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
            self.chats = [
                AIChat(
                    id=chat["id"],
                    title=chat.get("title", "New chat"),
                    messages=[AIMessage(**m) for m in chat.get("messages", [])],
                )
                for chat in data
            ]
        except Exception:
            self.chats = []

    def save(self):
        payload = [
            {
                "id": c.id,
                "title": c.title,
                "messages": [asdict(m) for m in c.messages],
            }
            for c in self.chats
        ]
        self.file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def create_chat(self, title: str = "New chat") -> AIChat:
        chat = AIChat(id=str(uuid.uuid4()), title=title, messages=[])
        self.chats.insert(0, chat)
        self.save()
        return chat

    def delete_chat(self, chat_id: str):
        self.chats = [c for c in self.chats if c.id != chat_id]
        self.save()

    def rename_chat(self, chat_id: str, new_title: str):
        for c in self.chats:
            if c.id == chat_id:
                c.title = new_title
                break
        self.save()

    def add_message(self, chat_id: str, role: str, content: str):
        for c in self.chats:
            if c.id == chat_id:
                c.messages.append(AIMessage(role=role, content=content))
                break
        self.save()

    def get_chat(self, chat_id: str) -> AIChat | None:
        for c in self.chats:
            if c.id == chat_id:
                return c
        return None
