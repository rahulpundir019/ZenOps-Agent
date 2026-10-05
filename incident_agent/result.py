from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class PipelineResult:
    texts_by_author: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    tool_calls: list[str] = field(default_factory=list)

    def last_text(self, author: str) -> str:
        parts = self.texts_by_author.get(author, [])
        return parts[-1] if parts else ""

    def combined_text(self) -> str:
        chunks = []
        for author, texts in self.texts_by_author.items():
            for text in texts:
                chunks.append(f"[{author}] {text}")
        return "\n\n".join(chunks)


def record_event(result: PipelineResult, event) -> None:
    if not event.content or not event.content.parts:
        return
    for part in event.content.parts:
        if part.text:
            result.texts_by_author[event.author].append(part.text)
        if part.function_call:
            result.tool_calls.append(part.function_call.name)
