import pytest
import subprocess
import sys
from datetime import datetime


def run_tests():
    """Запуск всех тестов с генерацией отчета"""
    print("=== Запуск автотестов системы синхронизации ===")
    print(f"Время запуска: {datetime.now()}")

    # Параметры pytest
    pytest_args = [
        "test_sync_scenarios.py",
        "-v",  # Подробный вывод
        "--html=test_report.html",  # HTML отчет
        "--self-contained-html",
        "--capture=sys"  # Для вывода print
    ]

    # Запуск тестов
    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        print("\n✅ Все тесты прошли успешно!")
    else:
        print(f"\n❌ Часть тестов не прошла. Код выхода: {exit_code}")

    print(f"\nОтчет сохранен в: test_report.html")
    return exit_code


if __name__ == "__main__":
    result = run_tests()
    sys.exit(result)