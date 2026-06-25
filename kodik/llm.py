"""
Работа с LLM и общие helper-функции для узлов.
"""
from __future__ import annotations

import json
from textwrap import dedent
from urllib import error, request

from .models import KodikState, OllamaSettings


class OllamaClient:
    """
    Очень тонкий HTTP-клиент для Ollama.
    """

    def __init__(self, settings: OllamaSettings | None = None):
        self.settings = settings or OllamaSettings()

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Отправляет один синхронный запрос в Ollama и возвращает текст ответа.
        """

        payload = {
            "model": self.settings.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": self.settings.temperature,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.settings.base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.settings.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except (error.URLError, TimeoutError, ConnectionError) as exc:
            raise RuntimeError(
                "Не удалось обратиться к Ollama. Подними локальный сервер и скачай модель qwen2.5:3b."
            ) from exc

        parsed = json.loads(raw)
        return parsed.get("response", "").strip()


def rag_stub(state: KodikState) -> str:
    """
    Временная заглушка для RAG-слоя.
    """

    intent = state.get("intent", {})
    profile = state.get("project_profile", {})
    return dedent(
        f"""
        Контекст проекта:
        - Вертикаль: {state.get("vertical", "не указана")}
        - Идея: {intent.get("idea", "не указана")}
        - Рынок: {intent.get("target_market", "не указан")}
        - Страна: {intent.get("country", "не указана")}
        - Горизонт: {intent.get("horizon_months", "не указан")} месяцев
        - Размер команды: {profile.get("team_size", "не указан")}
        - Runway: {profile.get("runway", "не указан")}
        - Аппетит к риску: {profile.get("risk_appetite", "не указан")}

        Заглушка доменного знания:
        - Для новых IT-продуктов типичны риски слабого PMF, дорогого привлечения,
          переоценки спроса и слишком длинной разработки до первой проверки рынка.
        - Для РФ можно учитывать волатильность спроса, изменения стоимости трафика,
          усиление конкуренции и внешние ограничения.
        """
    ).strip()


def ask_ollama(
    state: KodikState,
    node_name: str,
    system_prompt: str,
    user_prompt: str,
    fallback: str,
) -> tuple[str, list[str]]:
    """
    Единая обертка над вызовом LLM для всех узлов.
    """

    audit_log = state.get("audit_log", []).copy()
    try:
        text = OllamaClient().generate(system_prompt=system_prompt, user_prompt=user_prompt)
        audit_log.append(f"{node_name}: получен ответ от Ollama.")
        return text, audit_log
    except RuntimeError as exc:
        audit_log.append(f"{node_name}: Ollama недоступна, использована заглушка. {exc}")
        return fallback, audit_log
