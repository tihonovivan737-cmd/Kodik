"""
Пакет KODIK.

Здесь собраны все основные части системы:
- типы и состояние графа;
- LLM-клиент и вспомогательные функции;
- узлы LangGraph;
- сборка графа;
- демо-запуск.
"""

from .demo import build_demo_state, run_demo
from .graph import build_graph

__all__ = ["build_demo_state", "build_graph", "run_demo"]
