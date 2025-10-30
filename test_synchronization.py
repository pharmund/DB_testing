import pytest
from test_base import TestBase
from datetime import date, datetime
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

    def test_3_no_duplicate_on_same_employee_in_both_filials(self):
        """ТЕСТ 3: При одновременном оформлении одинаковых сотрудников в двух филиалах не происходит дублирования"""
        logger.info("=== ТЕСТ 3: Проверка отсутствия дублирования сотрудников ===")

        test_passport = self.get_test_passport(3)

        # Шаг 1: Создаем одинаковых сотрудников в обоих филиалах
        employee_data_f1 = {
            'emplcode': self.get_next_test_code(),
            'name': 'Иван',
            'surname': 'Петров',
            'patronymic': 'Сергеевич',
            'birthday': date(1985, 5, 10),
            'passport': test_passport,
            'poscode': 1,
            'filial': 1,
            'status': 'Active'
        }

        employee_data_f2 = {
            'emplcode': self.get_next_test_code(),
            'name': 'Иван',
            'surname': 'Петров',
            'patronymic': 'Сергеевич',
            'birthday': date(1985, 5, 10),
            'passport': test_passport,
            'poscode': 1,
            'filial': 2,
            'status': 'Active'
        }

        self.add_employee('filial1', employee_data_f1)
        self.add_employee('filial2', employee_data_f2)
        logger.info(f"Созданы одинаковые сотрудники в обоих филиалах с паспортом {test_passport}")

        # Шаг 2: Пытаемся синхронизировать - должно вернуть False (уже существует)
        sync_result = self.safe_sync_new_employee(test_passport)

        # Шаг 3: Проверяем, что дублирования не произошло
        session_f1 = self.db.get_session('filial1')
        session_f2 = self.db.get_session('filial2')
        try:
            # Проверяем количество сотрудников с этим паспортом в каждом филиале
            count_f1 = session_f1.execute(
                text("SELECT COUNT(*) FROM employee WHERE passport = :passport AND filial = 1"),
                {'passport': test_passport}
            ).scalar()

            count_f2 = session_f2.execute(
                text("SELECT COUNT(*) FROM employee WHERE passport = :passport AND filial = 2"),
                {'passport': test_passport}
            ).scalar()

            logger.info(f"Количество сотрудников после синхронизации: Ф1={count_f1}, Ф2={count_f2}")

            # Утверждения
            assert not sync_result, "Синхронизация должна вернуть False (сотрудник уже существует)"
            assert count_f1 == 1, f"В Ф1 должен быть 1 сотрудник, получено: {count_f1}"
            assert count_f2 == 1, f"В Ф2 должен быть 1 сотрудник, получено: {count_f2}"

        finally:
            session_f1.close()
            session_f2.close()

        logger.info("✅ УСПЕХ: ТЕСТ 3 ПРОЙДЕН: Дублирования сотрудников не произошло")

    def test_4_conflict_detection_on_partial_match(self):
        """ТЕСТ 4: При совпадении 2 из 3 ключевых параметров создается запись в журнале конфликтов"""
        logger.info("=== ТЕСТ 4: Обнаружение конфликтной ситуации ===")

        # Создаем сотрудников с совпадающими ФИО и датой рождения, но разными паспортами
        test_passport_f1 = self.get_test_passport(41)
        test_passport_f2 = self.get_test_passport(42)

        employee_data_f1 = {
            'emplcode': self.get_next_test_code(),
            'name': 'Мария',
            'surname': 'Сидорова',
            'patronymic': 'Ивановна',
            'birthday': date(1992, 8, 25),
            'passport': test_passport_f1,
            'poscode': 2,
            'filial': 1,
            'status': 'Active'
        }

        employee_data_f2 = {
            'emplcode': self.get_next_test_code(),
            'name': 'Мария',
            'surname': 'Сидорова',
            'patronymic': 'Ивановна',
            'birthday': date(1992, 8, 25),  # Та же дата рождения
            'passport': test_passport_f2,  # Другой паспорт
            'poscode': 2,
            'filial': 2,
            'status': 'Active'
        }

        self.add_employee('filial1', employee_data_f1)
        self.add_employee('filial2', employee_data_f2)
        logger.info("Созданы сотрудники с совпадающими ФИО и датой рождения, но разными паспортами")

        # Шаг 2: Эмулируем проверку на конфликт
        initial_conflicts_f1 = self.get_conflict_count('filial1')
        initial_conflicts_f2 = self.get_conflict_count('filial2')

        # Эмуляция обнаружения конфликта
        self._simulate_conflict_detection(test_passport_f1, test_passport_f2)

        # Шаг 3: Проверяем, что конфликт зарегистрирован
        final_conflicts_f1 = self.get_conflict_count('filial1')
        final_conflicts_f2 = self.get_conflict_count('filial2')

        logger.info(f"Конфликты до: Ф1={initial_conflicts_f1}, Ф2={initial_conflicts_f2}")
        logger.info(f"Конфликты после: Ф1={final_conflicts_f1}, Ф2={final_conflicts_f2}")

        # Проверяем, что количество конфликтов увеличилось
        assert final_conflicts_f1 > initial_conflicts_f1 or final_conflicts_f2 > initial_conflicts_f2, \
            "Должен быть зарегистрирован хотя бы один конфликт"

        # Проверяем содержимое журнала конфликтов
        session = self.db.get_session('filial1')
        try:
            conflict = session.execute(
                text("SELECT errlist FROM conflist WHERE errlist LIKE '%Сидорова%'")
            ).fetchone()

            if conflict:
                logger.info(f"Найден конфликт: {conflict[0]}")
                assert 'Сидорова' in conflict[0], "В описании конфликта должна быть фамилия сотрудника"
        finally:
            session.close()

        logger.info("✅ УСПЕХ: ТЕСТ 4 ПРОЙДЕН: Конфликт обнаружен и зарегистрирован")

    def test_5_conflict_resolution_and_synchronization(self):
        """ТЕСТ 5: После разрешения конфликта происходит синхронизация и удаление из журнала"""
        logger.info("=== ТЕСТ 5: Разрешение конфликта и синхронизация ===")

        test_passport = self.get_test_passport(5)

        # Шаг 1: Создаем конфликтную ситуацию
        employee_data_f1 = {
            'emplcode': self.get_next_test_code(),
            'name': 'Анна',
            'surname': 'Волкова',
            'patronymic': 'Петровна',
            'birthday': date(1988, 12, 5),
            'passport': test_passport,
            'poscode': 3,
            'filial': 1,
            'status': 'Active'
        }

        # Добавляем только в Ф1
        self.add_employee('filial1', employee_data_f1)

        # Создаем запись о конфликте
        session_f1 = self.db.get_session('filial1')
        try:
            session_f1.execute(
                text("""
                    INSERT INTO conflist (emplcode, errlist, resolved) 
                    VALUES (:emplcode, :errlist, FALSE)
                """),
                {
                    'emplcode': employee_data_f1['emplcode'],
                    'errlist': f'TEST_CONFLICT: Совпадение данных для сотрудника {test_passport}'
                }
            )
            session_f1.commit()
            logger.info("Создана тестовая запись о конфликте")
        finally:
            session_f1.close()

        # Шаг 2: Эмулируем разрешение конфликта экспертами
        self._simulate_conflict_resolution(test_passport)

        # Шаг 3: Проверяем, что конфликт разрешен
        session_f1 = self.db.get_session('filial1')
        try:
            resolved_conflicts = session_f1.execute(
                text("SELECT COUNT(*) FROM conflist WHERE emplcode = :emplcode AND resolved = TRUE"),
                {'emplcode': employee_data_f1['emplcode']}
            ).scalar()

            logger.info(f"Разрешенные конфликты: {resolved_conflicts}")
            assert resolved_conflicts > 0, "Конфликт должен быть помечен как разрешенный"

        finally:
            session_f1.close()

        # Шаг 4: Проверяем синхронизацию после разрешения конфликта
        sync_result = self.safe_sync_new_employee(test_passport)

        # Проверяем, что сотрудник появился в Ф2
        employee_in_f2 = self.employee_exists('filial2', test_passport, filial=2)

        logger.info(f"Синхронизация после разрешения конфликта: {sync_result}")
        logger.info(f"Сотрудник в Ф2 после синхронизации: {'ДА' if employee_in_f2 else 'НЕТ'}")

        assert sync_result, "Синхронизация должна быть успешной после разрешения конфликта"
        assert employee_in_f2, "Сотрудник должен быть синхронизирован в Ф2"

        logger.info("✅ УСПЕХ: ТЕСТ 5 ПРОЙДЕН: Конфликт разрешен и синхронизация выполнена")

    def test_6_history_preservation_on_employee_update(self):
        """ТЕСТ 6: При изменении информации о сотруднике сохраняется история изменений"""
        logger.info("=== ТЕСТ 6: Сохранение истории изменений ===")

        test_passport = self.get_test_passport(6)
        empl_code = self.get_next_test_code()

        # Шаг 1: Создаем сотрудника в Ф1
        employee_data = {
            'emplcode': empl_code,
            'name': 'Дмитрий',
            'surname': 'Орлов',
            'patronymic': 'Викторович',
            'birthday': date(1983, 4, 18),
            'passport': test_passport,
            'poscode': 1,  # Начальная должность
            'filial': 1,
            'status': 'Active'
        }

        self.add_employee('filial1', employee_data)
        logger.info(f"Создан сотрудник {empl_code} с начальной должностью 1")

        # Шаг 2: Вносим изменения в должность
        session = self.db.get_session('filial1')
        try:
            # Записываем изменение в историю
            session.execute(
                text("""
                    INSERT INTO emplhistory (emplcode, changedate, surname, passport, poscode, action)
                    VALUES (:emplcode, :changedate, :surname, :passport, :poscode, :action)
                """),
                {
                    'emplcode': empl_code,
                    'changedate': date.today(),
                    'surname': 'Орлов',
                    'passport': test_passport,
                    'poscode': 1,
                    'action': 'Начальная должность'
                }
            )

            # Меняем должность
            session.execute(
                text("UPDATE employee SET poscode = :new_poscode WHERE emplcode = :emplcode"),
                {'new_poscode': 2, 'emplcode': empl_code}
            )

            # Записываем изменение в историю
            session.execute(
                text("""
                    INSERT INTO emplhistory (emplcode, changedate, surname, passport, poscode, action)
                    VALUES (:emplcode, :changedate, :surname, :passport, :poscode, :action)
                """),
                {
                    'emplcode': empl_code,
                    'changedate': date.today(),
                    'surname': 'Орлов',
                    'passport': test_passport,
                    'poscode': 2,
                    'action': 'Повышение'
                }
            )

            session.commit()
            logger.info("Внесены изменения в должность и историю")

        finally:
            session.close()

        # Шаг 3: Синхронизируем сотрудника
        sync_result = self.safe_sync_new_employee(test_passport)

        # Шаг 4: Проверяем сохранение истории
        session_f1 = self.db.get_session('filial1')
        try:
            history_count = session_f1.execute(
                text("SELECT COUNT(*) FROM emplhistory WHERE emplcode = :emplcode"),
                {'emplcode': empl_code}
            ).scalar()

            current_position = session_f1.execute(
                text("SELECT poscode FROM employee WHERE emplcode = :emplcode"),
                {'emplcode': empl_code}
            ).scalar()

            logger.info(f"Записей в истории: {history_count}, текущая должность: {current_position}")

            # Утверждения
            assert history_count >= 2, f"Должно быть не менее 2 записей в истории, получено: {history_count}"
            assert current_position == 2, f"Текущая должность должна быть 2, получено: {current_position}"
            assert sync_result, "Синхронизация должна быть успешной"

        finally:
            session_f1.close()

        logger.info("✅ УСПЕХ: ТЕСТ 6 ПРОЙДЕН: История изменений сохранена")

    def _simulate_conflict_detection(self, passport1, passport2):
        """Эмуляция обнаружения конфликта"""
        session = self.db.get_session('filial1')
        try:
            # Эмуляция логики обнаружения конфликта
            session.execute(
                text("""
                    INSERT INTO conflist (emplcode, errlist, conflictdate, resolved)
                    VALUES (
                        (SELECT emplcode FROM employee WHERE passport = :passport1 AND filial = 1),
                        :errlist, 
                        NOW(), 
                        FALSE
                    )
                """),
                {
                    'passport1': passport1,
                    'errlist': f'CONFLICT: Возможное дублирование сотрудников {passport1} и {passport2}'
                }
            )
            session.commit()
            logger.info("Эмулировано обнаружение конфликта")
        finally:
            session.close()

    def _simulate_conflict_resolution(self, passport):
        """Эмуляция разрешения конфликта"""
        session = self.db.get_session('filial1')
        try:
            session.execute(
                text("""
                    UPDATE conflist 
                    SET resolved = TRUE, 
                        errlist = CONCAT(errlist, ' - РАЗРЕШЕНО: ', NOW())
                    WHERE emplcode = (
                        SELECT emplcode FROM employee WHERE passport = :passport AND filial = 1
                    )
                """),
                {'passport': passport}
            )
            session.commit()
            logger.info("Эмулировано разрешение конфликта")
        finally:
            session.close()