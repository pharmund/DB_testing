import pytest
from test_base import TestBase
from datetime import date
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


class TestSynchronization(TestBase):

    def test_1_new_employee_sync(self):
        """ТЕСТ 1: Нанятый сотрудник в Ф1 после синхронизации доступен и в Ф2"""
        logger.info("=== ТЕСТ 1: Синхронизация нового сотрудника ===")

        # Шаг 0: Используем уникальные тестовые данные
        test_empl_code = self.get_next_test_code()
        test_passport = self.get_test_passport(1)

        # Проверяем, что такого сотрудника точно нет в базах
        employee_in_f1_before = self.employee_exists('filial1', test_passport)
        employee_in_f2_before = self.employee_exists('filial2', test_passport)

        if employee_in_f1_before or employee_in_f2_before:
            logger.warning(f"Сотрудник с паспортом {test_passport} уже существует в базах перед тестом!")
            # Используем другой паспорт
            test_passport = f'700{self.test_counter}700{self.test_counter}0'
            logger.info(f"Используем альтернативный паспорт: {test_passport}")

        # Запоминаем начальное состояние
        initial_f1_count = self.get_employee_count('filial1', filial=1)
        initial_f2_count = self.get_employee_count('filial2', filial=2)

        logger.info(f"Начальное состояние: Ф1={initial_f1_count}, Ф2={initial_f2_count}")
        logger.info(f"Используемый паспорт: {test_passport}")

        # Шаг 1: Добавляем нового сотрудника в Ф1
        employee_data = {
            'emplcode': test_empl_code,
            'name': 'Александр',
            'surname': 'Новиков',
            'patronymic': 'Владимирович',
            'birthday': date(1988, 7, 15),
            'passport': test_passport,
            'poscode': 2,
            'filial': 1,
            'status': 'Active'
        }

        self.add_employee('filial1', employee_data)
        logger.info(f"Добавлен сотрудник {test_empl_code} в Ф1 с паспортом {test_passport}")

        # Проверяем, что сотрудник добавлен только в Ф1
        after_add_f1_count = self.get_employee_count('filial1', filial=1)
        after_add_f2_count = self.get_employee_count('filial2', filial=2)

        logger.info(f"После добавления: Ф1={after_add_f1_count}, Ф2={after_add_f2_count}")

        assert after_add_f1_count == initial_f1_count + 1, f"Сотрудник не добавлен в Ф1. Ожидалось: {initial_f1_count + 1}, Получено: {after_add_f1_count}"
        assert after_add_f2_count == initial_f2_count, f"В Ф2 не должно быть изменений до синхронизации. Ожидалось: {initial_f2_count}, Получено: {after_add_f2_count}"

        # Проверяем, что сотрудник действительно есть в Ф1 и нет в Ф2
        employee_in_f1_before_sync = self.employee_exists('filial1', test_passport, filial=1)
        employee_in_f2_before_sync = self.employee_exists('filial2', test_passport, filial=2)

        logger.info(
            f"Перед синхронизацией: в Ф1={'ДА' if employee_in_f1_before_sync else 'НЕТ'}, в Ф2={'ДА' if employee_in_f2_before_sync else 'НЕТ'}")

        assert employee_in_f1_before_sync, "Сотрудник должен быть в Ф1 перед синхронизацией"
        assert not employee_in_f2_before_sync, "Сотрудник не должен быть в Ф2 перед синхронизацией"

        # Шаг 2: Безопасная синхронизация - только из Ф1 в Ф2
        sync_result = self.safe_sync_new_employee(test_passport)
        logger.info(f"Синхронизация выполнена: {sync_result}")

        # Шаг 3: Проверяем результат
        final_f1_count = self.get_employee_count('filial1', filial=1)
        final_f2_count = self.get_employee_count('filial2', filial=2)

        employee_in_f1_after_sync = self.employee_exists('filial1', test_passport, filial=1)
        employee_in_f2_after_sync = self.employee_exists('filial2', test_passport, filial=2)

        logger.info(f"Конечное состояние: Ф1={final_f1_count}, Ф2={final_f2_count}")
        logger.info(
            f"После синхронизации: в Ф1={'ДА' if employee_in_f1_after_sync else 'НЕТ'}, в Ф2={'ДА' if employee_in_f2_after_sync else 'НЕТ'}")

        # Проверяем утверждения
        assert sync_result, "Синхронизация должна быть успешной"
        assert employee_in_f2_after_sync, "Сотрудник не синхронизирован в Ф2"
        assert final_f1_count == initial_f1_count + 1, f"Неверное количество сотрудников в Ф1. Ожидалось: {initial_f1_count + 1}, Получено: {final_f1_count}"
        assert final_f2_count == initial_f2_count + 1, f"Неверное количество сотрудников в Ф2. Ожидалось: {initial_f2_count + 1}, Получено: {final_f2_count}"

        logger.info("✅ УСПЕХ: ТЕСТ 1 ПРОЙДЕН: Сотрудник успешно синхронизирован")

    def test_2_employee_dismissal_sync(self):
        """ТЕСТ 2: Уволенный сотрудник в Ф2 после синхронизации уволен и в Ф1"""
        logger.info("=== ТЕСТ 2: Синхронизация увольнения ===")

        # Используем уникальные тестовые данные
        test_passport = self.get_test_passport(2)
        empl_code_f1 = self.get_next_test_code()
        empl_code_f2 = self.get_next_test_code()

        # Проверяем, что такого сотрудника точно нет в базах
        employee_exists = self.employee_exists('filial1', test_passport) or self.employee_exists('filial2',
                                                                                                 test_passport)
        if employee_exists:
            logger.warning(f"Сотрудник с паспортом {test_passport} уже существует в базах перед тестом!")
            # Используем другой паспорт
            test_passport = f'700{self.test_counter}700{self.test_counter}0'
            logger.info(f"Используем альтернативный паспорт: {test_passport}")

        # Шаг 1: Создаем сотрудника в обоих филиалах
        employee_data_f1 = {
            'emplcode': empl_code_f1,
            'name': 'Ольга',
            'surname': 'Кузнецова',
            'patronymic': 'Андреевна',
            'birthday': date(1990, 3, 20),
            'passport': test_passport,
            'poscode': 3,
            'filial': 1,
            'status': 'Active'
        }

        employee_data_f2 = {
            'emplcode': empl_code_f2,
            'name': 'Ольга',
            'surname': 'Кузнецова',
            'patronymic': 'Андреевна',
            'birthday': date(1990, 3, 20),
            'passport': test_passport,
            'poscode': 3,
            'filial': 2,
            'status': 'Active'
        }

        self.add_employee('filial1', employee_data_f1)
        self.add_employee('filial2', employee_data_f2)
        logger.info(f"Создан сотрудник в обоих филиалах с паспортом {test_passport}")

        # Проверяем начальные статусы
        session_f1 = self.db.get_session('filial1')
        session_f2 = self.db.get_session('filial2')
        try:
            status_f1 = session_f1.execute(
                text("SELECT status FROM employee WHERE passport = :passport AND filial = 1"),
                {'passport': test_passport}
            ).scalar()

            status_f2 = session_f2.execute(
                text("SELECT status FROM employee WHERE passport = :passport AND filial = 2"),
                {'passport': test_passport}
            ).scalar()

            logger.info(f"Начальные статусы: Ф1={status_f1}, Ф2={status_f2}")
            assert status_f1 == 'Active', "Начальный статус в Ф1 должен быть Active"
            assert status_f2 == 'Active', "Начальный статус в Ф2 должен быть Active"
        finally:
            session_f1.close()
            session_f2.close()

        # Шаг 2: Увольняем сотрудника в Ф2
        session = self.db.get_session('filial2')
        try:
            session.execute(
                text("UPDATE employee SET status = 'Fired' WHERE passport = :passport AND filial = 2"),
                {'passport': test_passport}
            )
            session.commit()
            logger.info("Сотрудник уволен в Ф2")
        finally:
            session.close()

        # Проверяем статус после увольнения в Ф2
        session_f2_after = self.db.get_session('filial2')
        try:
            status_f2_after = session_f2_after.execute(
                text("SELECT status FROM employee WHERE passport = :passport AND filial = 2"),
                {'passport': test_passport}
            ).scalar()
            logger.info(f"Статус в Ф2 после увольнения: {status_f2_after}")
            assert status_f2_after == 'Fired', "Статус в Ф2 должен быть Fired после увольнения"
        finally:
            session_f2_after.close()

        # Шаг 3: Безопасная синхронизация увольнения
        sync_result = self.safe_sync_dismissal(test_passport)
        logger.info(f"Синхронизация увольнения выполнена: {sync_result}")

        # Шаг 4: Проверяем результат
        session_f1_final = self.db.get_session('filial1')
        try:
            result = session_f1_final.execute(
                text("SELECT status FROM employee WHERE passport = :passport AND filial = 1"),
                {'passport': test_passport}
            )
            status_in_f1 = result.scalar()
        finally:
            session_f1_final.close()

        logger.info(f"Статус сотрудника в Ф1 после синхронизации: {status_in_f1}")

        assert status_in_f1 == 'Fired', f"Статус увольнения не синхронизирован. Ожидалось: Fired, Получено: {status_in_f1}"

        logger.info("✅ УСПЕХ: ТЕСТ 2 ПРОЙДЕН: Статус увольнения синхронизирован")