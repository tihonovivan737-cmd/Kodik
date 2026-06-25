"""
LangGraph nodes and routing helpers for KODIK.
"""
from __future__ import annotations

from .llm import ask_ollama, rag_stub
from .models import Decision, KodikState
from .prompts import get_prompt, render_prompt


def intention_node(state: KodikState) -> KodikState:
    rag_context = rag_stub(state)
    intent = state.get("intent", {})

    system_prompt = get_prompt("intention.system")
    user_prompt = render_prompt(
        "intention.user",
        idea=intent.get("idea", "не указана"),
        target_market=intent.get("target_market", "не указан"),
        country=intent.get("country", "не указана"),
        horizon_months=intent.get("horizon_months", "не указан"),
        investment_size=intent.get("investment_size", "не указана"),
        expected_upside=intent.get("expected_upside", "не указан"),
        rag_context=rag_context,
    )
    fallback = get_prompt("intention.fallback")

    text, audit_log = ask_ollama(state, "Намерение", system_prompt, user_prompt, fallback)
    return {
        "rag_context": rag_context,
        "intention_summary": text,
        "audit_log": audit_log,
        "iteration": state.get("iteration", 0),
        "max_iterations": state.get("max_iterations", 2),
        "trust_score": state.get("trust_score", 0.5),
    }


def environment_node(state: KodikState) -> KodikState:
    system_prompt = get_prompt("environment.system")
    user_prompt = render_prompt(
        "environment.user",
        intention_summary=state.get("intention_summary", "нет данных"),
        rag_context=state.get("rag_context", "нет данных"),
    )
    fallback = get_prompt("environment.fallback")

    text, audit_log = ask_ollama(state, "Среда", system_prompt, user_prompt, fallback)

    current_iteration = state.get("iteration", 0)
    if state.get("threshold_decision") == Decision.HOLD:
        current_iteration += 1

    return {
        "environment_brief": text,
        "audit_log": audit_log,
        "iteration": current_iteration,
    }


def destructor_node(state: KodikState) -> KodikState:
    system_prompt = get_prompt("destructor.system")
    user_prompt = render_prompt(
        "destructor.user",
        intention_summary=state.get("intention_summary", "нет данных"),
        environment_brief=state.get("environment_brief", "нет данных"),
    )
    fallback = get_prompt("destructor.fallback")

    text, audit_log = ask_ollama(state, "Деструктор", system_prompt, user_prompt, fallback)
    return {
        "destructor_brief": text,
        "audit_log": audit_log,
    }


def threshold_node(state: KodikState) -> KodikState:
    iteration = state.get("iteration", 0)
    trust_score = state.get("trust_score", 0.5)

    if iteration == 0:
        decision = Decision.RUN_EXPERIMENT
        fallback_reason = "Реальных данных еще нет, значит сначала нужен дешевый обратимый эксперимент."
    elif trust_score >= 0.7:
        decision = Decision.SCALE
        fallback_reason = "Прогнозы начали подтверждаться, можно увеличивать ставку."
    elif iteration < state.get("max_iterations", 2):
        decision = Decision.HOLD
        fallback_reason = "Сигналы смешанные, продолжаем малыми шагами."
    else:
        decision = Decision.EXIT
        fallback_reason = "У ставки недостаточно доказательств, чтобы идти дальше."

    system_prompt = get_prompt("threshold.system")
    user_prompt = render_prompt(
        "threshold.user",
        intention_summary=state.get("intention_summary", "нет данных"),
        environment_brief=state.get("environment_brief", "нет данных"),
        destructor_brief=state.get("destructor_brief", "нет данных"),
        iteration=iteration,
        trust_score=trust_score,
        decision=decision.value,
    )

    text, audit_log = ask_ollama(state, "Порог", system_prompt, user_prompt, fallback_reason)
    audit_log.append(f"Порог: принято решение '{decision.value}'.")
    return {
        "threshold_decision": decision,
        "threshold_reasoning": text,
        "audit_log": audit_log,
    }


def experiment_node(state: KodikState) -> KodikState:
    system_prompt = get_prompt("experiment.system")
    user_prompt = render_prompt(
        "experiment.user",
        intention_summary=state.get("intention_summary", "нет данных"),
        destructor_brief=state.get("destructor_brief", "нет данных"),
    )
    fallback = get_prompt("experiment.fallback")

    text, audit_log = ask_ollama(state, "Эксперимент", system_prompt, user_prompt, fallback)
    audit_log.append("Эксперимент: предложен минимальный проверяющий шаг.")

    return {
        "cheapest_experiment": {
            "name": "Минимальный проверяющий шаг",
            "cost": "Низкая стоимость",
            "reversibility": "high",
            "success_signal": text,
        },
        "audit_log": audit_log,
    }


def calibration_node(state: KodikState) -> KodikState:
    history = state.get("calibration_history", []).copy()
    history.append(
        {
            "prediction": "Ожидался положительный первичный сигнал спроса.",
            "actual": "Заглушка: часть пользователей проявила интерес.",
            "deviation": "Умеренное отклонение.",
            "confidence_delta": 0.15,
        }
    )

    trust_score = min(1.0, state.get("trust_score", 0.5) + 0.15)
    next_iteration = state.get("iteration", 0) + 1
    audit_log = state.get("audit_log", []).copy()
    audit_log.append("Калибровка: обновлено доверие на основе заглушки результата.")
    audit_log.append(f"Калибровка: число завершенных циклов увеличено до {next_iteration}.")

    return {
        "calibration_history": history,
        "trust_score": trust_score,
        "iteration": next_iteration,
        "audit_log": audit_log,
    }


def route_after_threshold(state: KodikState) -> str:
    decision = state["threshold_decision"]
    if decision == Decision.RUN_EXPERIMENT:
        return "experiment"
    if decision == Decision.HOLD:
        return "environment"
    return "finish"


def route_after_calibration(state: KodikState) -> str:
    return "threshold"


def finalize_node(state: KodikState) -> KodikState:
    audit_log = state.get("audit_log", []).copy()
    audit_log.append("Финализация: граф дошел до конечного решения.")
    return {
        "done": True,
        "audit_log": audit_log,
    }
