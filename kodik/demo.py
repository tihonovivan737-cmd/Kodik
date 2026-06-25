"""
Демо-сценарий запуска графа KODIK.
"""
from __future__ import annotations

from .graph import build_graph
from .models import Decision, KodikState


def build_demo_state() -> KodikState:
    """
    Собирает демонстрационное начальное состояние.
    """

    return {
        "session_id": "demo-session",
        "vertical": "Запуск новой IT-фичи",
        "intent": {
            "idea": "AI-ассистент для product discovery внутри B2B SaaS",
            "target_market": "B2B SaaS",
            "country": "Россия",
            "horizon_months": 6,
            "investment_type": "hybrid",
            "investment_size": "4 человеко-месяца и небольшой маркетинговый бюджет",
            "expected_upside": "новая выручка и рост удержания клиентов",
        },
        "project_profile": {
            "team_size": "4",
            "runway": "6 месяцев",
            "risk_appetite": "средний",
        },
        "audit_log": [],
        "calibration_history": [],
        "iteration": 0,
        "max_iterations": 2,
        "trust_score": 0.5,
    }


def run_demo() -> KodikState:
    """
    Запускает демонстрационный прогон и печатает обновления по мере выполнения.
    """

    graph = build_graph()
    initial_state = build_demo_state()

    state = initial_state
    for chunk in graph.stream(initial_state, stream_mode="updates"):
        for node_name, update in chunk.items():
            print(f"\n{'=' * 40}")
            print(f"Узел: [{node_name.upper()}]")
            print(f"{'=' * 40}")

            if "intention_summary" in update:
                print(f"--> Сформирована ставка:\n{update['intention_summary']}")
            if "environment_brief" in update:
                print(f"--> Анализ среды:\n{update['environment_brief']}")
            if "destructor_brief" in update:
                print(f"--> Атака деструктора:\n{update['destructor_brief']}")
            if "threshold_decision" in update:
                print(f"--> Решение порога: {update['threshold_decision'].value}")
                print(f"--> Обоснование:\n{update['threshold_reasoning']}")
            if "cheapest_experiment" in update:
                print(f"--> Эксперимент: {update['cheapest_experiment']['name']}")
                print(f"--> Сигнал успеха:\n{update['cheapest_experiment']['success_signal']}")
            if "trust_score" in update:
                print(f"--> Обновлен Trust Score: {update['trust_score']}")

            state = {**state, **update}

    return state


def print_demo_result(result: KodikState) -> None:
    """
    Печатает финальную сводку после демо-запуска.
    """

    print("\n" + "#" * 50)
    print("ФИНАЛЬНЫЙ РЕЗУЛЬТАТ РАБОТЫ ГРАФА")
    print("#" * 50)

    final_decision = result.get("threshold_decision")
    decision_value = final_decision.value if isinstance(final_decision, Decision) else final_decision

    print(f"Итоговое решение: {decision_value}")
    print(f"Итераций пройдено: {result.get('iteration')}")
    print(f"Итоговый Trust Score: {result.get('trust_score')}")
