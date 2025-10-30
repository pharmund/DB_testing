#!/usr/bin/env python3
import pytest
import logging
import sys
import os
from datetime import datetime


def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
        ]
    )


def main():
    """Основная функция запуска тестов"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("ЗАПУСК ТЕСТОВ СИНХРОНИЗАЦИИ БАЗ ДАННЫХ")

    # Запуск pytest
    pytest_args = [
        'test_synchronization.py',
        '-v',
        '--tb=short',
        '--color=yes'
    ]

    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        logger.info("ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
    else:
        logger.error(f"НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ. Код выхода: {exit_code}")

    return exit_code


if __name__ == '__main__':
    sys.exit(main())