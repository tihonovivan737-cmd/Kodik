"""
Загрузка prompt-шаблонов из Markdown-файла.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROMPTS_PATH = Path(__file__).with_name("prompts.md")


@lru_cache(maxsize=1)
def load_prompt_sections() -> dict[str, str]:
    """
    Читает `prompts.md` и разбивает его на секции по заголовкам `##`.
    """

    content = PROMPTS_PATH.read_text(encoding="utf-8")
    sections: dict[str, list[str]] = {}
    current_name: str | None = None

    for raw_line in content.splitlines():
        if raw_line.startswith("## "):
            current_name = raw_line[3:].strip()
            sections[current_name] = []
            continue

        if current_name is not None:
            sections[current_name].append(raw_line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def get_prompt(name: str) -> str:
    """
    Возвращает сырую секцию prompt-файла по имени.
    """

    sections = load_prompt_sections()
    if name not in sections:
        raise KeyError(f"Prompt section '{name}' not found in {PROMPTS_PATH.name}")
    return sections[name]


def render_prompt(name: str, **context: object) -> str:
    """
    Возвращает prompt-секцию с подстановкой контекста через `str.format`.
    """

    return get_prompt(name).format(**context).strip()
