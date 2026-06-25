"""
Точка входа для демонстрационного запуска KODIK.

Основная логика вынесена в пакет `kodik`, чтобы код было проще читать,
тестировать и расширять без роста одного монолитного файла.
"""
from __future__ import annotations

from kodik.demo import print_demo_result, run_demo


if __name__ == "__main__":
    print("Запуск графа KODIK с выводом промежуточных этапов...\n")
    result = run_demo()
    print_demo_result(result)
