"""
Базовые типы и структуры данных KODIK.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, TypedDict


class Decision(str, Enum):
    """
    Набор допустимых решений, которые может принять арбитр (`threshold_node`).
    """

    RUN_EXPERIMENT = "run_experiment"
    HOLD = "hold"
    SCALE = "scale"
    EXIT = "exit"


class BetIntent(TypedDict, total=False):
    """
    Структурированное описание исходной продуктовой идеи.
    """

    idea: str
    target_market: str
    country: str
    horizon_months: int
    investment_type: Literal["money", "team_weeks", "hybrid"]
    investment_size: str
    expected_upside: str
    assumptions: list[str]


class ExperimentStep(TypedDict, total=False):
    """
    Описание минимального эксперимента, которым мы хотим проверить гипотезу.
    """

    name: str
    cost: str
    reversibility: Literal["high", "medium", "low"]
    success_signal: str


class CalibrationRecord(TypedDict, total=False):
    """
    Одна запись истории калибровки.
    """

    prediction: str
    actual: str
    deviation: str
    confidence_delta: float


class KodikState(TypedDict, total=False):
    """
    Единое состояние всего графа.
    """

    session_id: str
    vertical: str
    intent: BetIntent
    project_profile: dict[str, str]
    rag_context: str
    intention_summary: str
    environment_brief: str
    destructor_brief: str
    threshold_reasoning: str
    threshold_decision: Decision
    cheapest_experiment: ExperimentStep
    calibration_history: list[CalibrationRecord]
    trust_score: float
    iteration: int
    max_iterations: int
    done: bool
    audit_log: list[str]


@dataclass
class OllamaSettings:
    """
    Настройки подключения к локальной Ollama.
    """

    model: str = "qwen2.5:3b"
    base_url: str = "http://127.0.0.1:11434"
    temperature: float = 0.2
    timeout_seconds: int = 90
