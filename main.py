from __future__ import annotations

"""
Каркас оркестрации для движка принятия решений KODIK.

Почему здесь LangGraph, а не только LangChain:
- у процесса есть общее состояние;
- в графе есть ветвления;
- после реального эксперимента нужен цикл обратной связи.

Одного LangChain достаточно для отдельных цепочек или агентов, но здесь
нужен явный граф, где узлы обмениваются общим состоянием, а узел
"Порог" умеет условно маршрутизировать выполнение.
"""

from enum import Enum
from typing import Literal, TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - позволяет импортировать файл без зависимостей
    END = "__end__"
    START = "__start__"
    StateGraph = None


class Decision(str, Enum):
    RUN_EXPERIMENT = "run_experiment"
    HOLD = "hold"
    SCALE = "scale"
    EXIT = "exit"


class BetIntent(TypedDict, total=False):
    idea: str
    target_market: str
    country: str
    horizon_months: int
    investment_type: Literal["money", "team_weeks", "hybrid"]
    investment_size: str
    expected_upside: str
    assumptions: list[str]


class EnvironmentScenario(TypedDict, total=False):
    name: str
    shock_class: str
    description: str
    severity: Literal["low", "medium", "high"]


class AttackVector(TypedDict, total=False):
    assumption: str
    scenario: str
    failure_mode: str
    survivable: bool
    loss_radius: str


class ExperimentStep(TypedDict, total=False):
    name: str
    cost: str
    reversibility: Literal["high", "medium", "low"]
    success_signal: str


class CalibrationRecord(TypedDict, total=False):
    prediction: str
    actual: str
    deviation: str
    confidence_delta: float


class KodikState(TypedDict, total=False):
    # Это общее состояние сессии, которое передаётся между всеми узлами графа.
    # Каждый узел читает только нужные поля и возвращает обновления, которые
    # LangGraph складывает обратно в общий контекст выполнения.
    session_id: str
    vertical: str
    intent: BetIntent
    project_profile: dict[str, str]
    environment_brief: str
    environment_scenarios: list[EnvironmentScenario]
    destructor_brief: str
    attack_vectors: list[AttackVector]
    cheapest_experiment: ExperimentStep
    threshold_decision: Decision
    threshold_reasoning: str
    calibration_history: list[CalibrationRecord]
    trust_score: float
    iteration: int
    max_iterations: int
    done: bool
    audit_log: list[str]


def intention_node(state: KodikState) -> KodikState:
    """Нормализует ставку и вытаскивает наружу явные допущения."""
    audit_log = state.get("audit_log", [])
    audit_log.append("Намерение: ставка формализована, ключевые допущения извлечены.")
    return {
        # На первом шаге инициализируем базовые поля цикла, чтобы дальше узлы
        # могли опираться на единый формат состояния.
        "audit_log": audit_log,
        "iteration": state.get("iteration", 0),
        "max_iterations": state.get("max_iterations", 2),
        "trust_score": state.get("trust_score", 0.5),
    }


def environment_node(state: KodikState) -> KodikState:
    """Генерирует внешние шоки под нишу, страну и временной горизонт."""
    audit_log = state.get("audit_log", [])
    audit_log.append("Среда: собраны внешние стресс-сценарии для текущей ставки.")
    return {
        # Здесь позже может жить агент, который строит набор угроз из RAG,
        # отраслевой базы кейсов или внешних источников знаний.
        "environment_brief": "Заглушка: угрозы ниши, макрошоки и внешние ограничения.",
        "environment_scenarios": state.get("environment_scenarios", []),
        "audit_log": audit_log,
    }


def destructor_node(state: KodikState) -> KodikState:
    """Атакует допущения через premortem-сценарии провала."""
    audit_log = state.get("audit_log", [])
    audit_log.append("Деструктор: найдены точки, в которых ставка ломается под давлением.")
    return {
        # Этот узел не выносит финальный приговор, а специально ищет самые
        # болезненные сценарии, чтобы Порог решал уже на основе честной атаки.
        "destructor_brief": "Заглушка: самые сильные сценарии провала для этой ставки.",
        "attack_vectors": state.get("attack_vectors", []),
        "audit_log": audit_log,
    }


def threshold_node(state: KodikState) -> KodikState:
    """
    Арбитр между движением дальше, удержанием ставки, масштабированием и выходом.

    В каркасе логика маршрутизации пока упрощённая:
    - если калибровки ещё не было -> запускаем самый дешёвый реальный эксперимент;
    - если после цикла доверие высокое -> разрешаем масштабирование;
    - иначе -> выходим.
    """
    iteration = state.get("iteration", 0)
    trust_score = state.get("trust_score", 0.5)

    if iteration == 0:
        decision = Decision.RUN_EXPERIMENT
        reasoning = "Реальных данных ещё нет, поэтому нужен самый дешёвый обратимый тест."
    elif trust_score >= 0.7:
        decision = Decision.SCALE
        reasoning = "Прогнозы достаточно согласуются с реальностью, можно увеличивать ставку."
    elif iteration < state.get("max_iterations", 2):
        decision = Decision.HOLD
        reasoning = "Сигналы смешанные, поэтому удерживаем размер ставки и идём на новый цикл."
    else:
        decision = Decision.EXIT
        reasoning = "Доверие не заслужило право на масштабирование, ставку лучше остановить."

    audit_log = state.get("audit_log", [])
    audit_log.append(f"Порог: принято решение '{decision.value}'.")
    return {
        "threshold_decision": decision,
        "threshold_reasoning": reasoning,
        "audit_log": audit_log,
    }


def experiment_node(state: KodikState) -> KodikState:
    """Описывает самый дешёвый реальный шаг, который разрешил Порог."""
    iteration = state.get("iteration", 0) + 1
    audit_log = state.get("audit_log", [])
    audit_log.append("Эксперимент: выполнен самый дешёвый обратимый шаг в реальности.")
    return {
        # После эксперимента увеличиваем номер итерации, чтобы Порог видел,
        # сколько циклов проверки ставка уже пережила.
        "iteration": iteration,
        "cheapest_experiment": state.get(
            "cheapest_experiment",
            {
                "name": "Заглушка эксперимента",
                "cost": "Низкая стоимость",
                "reversibility": "high",
                "success_signal": "Измеримая реакция пользователя",
            },
        ),
        "audit_log": audit_log,
    }


def calibration_node(state: KodikState) -> KodikState:
    """Сравнивает прогноз с фактом и обновляет доверие к системе."""
    history = state.get("calibration_history", [])
    history.append(
        {
            "prediction": "Заглушка прогноза",
            "actual": "Заглушка фактического результата",
            "deviation": "Отклонение станет известно после подключения реальных метрик",
            "confidence_delta": 0.2,
        }
    )

    # В каркасе доверие растёт искусственно, просто чтобы показать механику
    # обратной связи. Позже здесь должна быть реальная функция калибровки.
    trust_score = min(1.0, state.get("trust_score", 0.5) + 0.2)
    audit_log = state.get("audit_log", [])
    audit_log.append("Калибровка: прогноз сопоставлен с измеренным результатом.")
    return {
        "calibration_history": history,
        "trust_score": trust_score,
        "audit_log": audit_log,
    }


def route_after_threshold(state: KodikState) -> str:
    # Это главный маршрутизатор графа: он переводит решение Порога
    # в имя следующего узла, куда должен перейти процесс.
    decision = state["threshold_decision"]
    if decision == Decision.RUN_EXPERIMENT:
        return "experiment"
    if decision == Decision.HOLD:
        return "environment"
    return "finish"


def route_after_calibration(state: KodikState) -> str:
    # После калибровки мы возвращаемся к Порогу, чтобы заново оценить ставку
    # уже с учётом новых фактических данных.
    if state.get("iteration", 0) >= state.get("max_iterations", 2):
        return "threshold"
    return "threshold"


def finalize_node(state: KodikState) -> KodikState:
    audit_log = state.get("audit_log", [])
    audit_log.append("Финализация: граф дошёл до терминального решения.")
    return {"done": True, "audit_log": audit_log}


def build_graph():
    if StateGraph is None:
        raise ImportError(
            "langgraph не установлен. Сначала установите зависимость: pip install langgraph"
        )

    # Здесь описывается не бизнес-логика, а именно топология процесса:
    # какие узлы существуют и в какой последовательности между ними течёт state.
    graph = StateGraph(KodikState)
    graph.add_node("intention", intention_node)
    graph.add_node("environment", environment_node)
    graph.add_node("destructor", destructor_node)
    graph.add_node("threshold", threshold_node)
    graph.add_node("experiment", experiment_node)
    graph.add_node("calibration", calibration_node)
    graph.add_node("finalize", finalize_node)

    # Линейная часть первого прохода: формализуем ставку, затем собираем
    # давление среды, после чего атакуем ставку через Деструктора.
    graph.add_edge(START, "intention")
    graph.add_edge("intention", "environment")
    graph.add_edge("environment", "destructor")
    graph.add_edge("destructor", "threshold")

    # После Порога граф либо отправляет нас в реальный эксперимент,
    # либо запускает новый круг анализа, либо завершает процесс.
    graph.add_conditional_edges(
        "threshold",
        route_after_threshold,
        {
            "experiment": "experiment",
            "environment": "environment",
            "finish": "finalize",
        },
    )

    # Обратная связь после эксперимента: измеряем факт и возвращаемся
    # к Порогу уже с обновлённым уровнем доверия.
    graph.add_edge("experiment", "calibration")
    graph.add_conditional_edges(
        "calibration",
        route_after_calibration,
        {
            "threshold": "threshold",
        },
    )
    graph.add_edge("finalize", END)
    return graph.compile()


def describe_graph() -> str:
    return "\n".join(
        [
            "START -> intention -> environment -> destructor -> threshold",
            "threshold -> experiment -> calibration -> threshold",
            "threshold -> environment  (если вердикт HOLD / держим ставку маленькой)",
            "threshold -> finalize -> END  (если вердикт SCALE или EXIT)",
        ]
    )


if __name__ == "__main__":
    print("Каркас LangGraph для KODIK")
    print()
    print("Рекомендуемая архитектура: LangGraph, а не линейный пайплайн на LangChain.")
    print("Причина: общий state, условная маршрутизация и цикл обратной связи.")
    print()
    print(describe_graph())
