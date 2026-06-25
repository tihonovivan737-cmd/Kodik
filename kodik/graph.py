"""
Сборка и компиляция LangGraph-графа KODIK.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .models import KodikState
from .nodes import (
    calibration_node,
    destructor_node,
    environment_node,
    experiment_node,
    finalize_node,
    intention_node,
    route_after_calibration,
    route_after_threshold,
    threshold_node,
)


def build_graph():
    """
    Создает и компилирует LangGraph-граф.
    """

    graph = StateGraph(KodikState)

    graph.add_node("intention", intention_node)
    graph.add_node("environment", environment_node)
    graph.add_node("destructor", destructor_node)
    graph.add_node("threshold", threshold_node)
    graph.add_node("experiment", experiment_node)
    graph.add_node("calibration", calibration_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "intention")
    graph.add_edge("intention", "environment")
    graph.add_edge("environment", "destructor")
    graph.add_edge("destructor", "threshold")
    graph.add_conditional_edges(
        "threshold",
        route_after_threshold,
        {
            "experiment": "experiment",
            "environment": "environment",
            "finish": "finalize",
        },
    )
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
