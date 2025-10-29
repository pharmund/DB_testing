import pytest
from datetime import date, datetime
from test_base import BaseSyncTest


class TestSyncScenarios(BaseSyncTest):
    """Тестовые сценарии синхронизации"""

    def test_01_sync_new_employee_from_filial1(self):
        """Тест 1: Синхронизация нового сотрудника из Ф1 в Ф2"""
        print("\n=== Тест 1: Синхронизация нового сотрудника из Ф1 в Ф2 ===")

        # ШАГ 1: Подготовка
        initial_count_f2 = self.get_employee_count(config.db_filial2, filial=2)
        print(f"Начальное количество сотрудников в Ф2: {initial_count_f2}")

        # ШАГ 2: Добавляем нового сотрудника в Ф1
        new_employee = {
            'EmplCode': 1003,
            'Name': 'Сергей',
            'Surname': 'Козлов',
            'Patronymic': 'Алексеевич',
            'Birthday': date(1990, 5, 5),
            'Passport': '4444444444',
            'PosCode': 2,
            'Filial': 1
        }

        self.add_employee(config.db_filial1, new_employee)

        # Добавляем запись в историю
        history_data = {
            'EmplCode': 1003,
            'ChangeDate': date.today(),
            'Surname': 'Козлов',
            'Passport': '4444444444',
            'PosCode': 2,
            'Action': 'Hired'
        }
        self.add_employment_history(config.db_filial1, history_data)

        print("Добавлен новый сотрудник в Ф1")

        # ШАГ 3: Эмуляция синхронизации (в реальности здесь будет job)
        self.emulate_sync()

        # ШАГ 4: Проверка результатов
        final_count_f2 = self.get_employee_count(config.db_filial2, filial=2)
        conflict_count = self.get_conflict_count(config.db_filial2)

        print(f"Конечное количество сотрудников в Ф2: {final_count_f2}")
        print(f"Количество конфликтов: {conflict_count}")

        # Проверки
        assert final_count_f2 == initial_count_f2 + 1, "Количество сотрудников в Ф2 должно увеличиться на 1"
        assert conflict_count == 0, "Не должно быть конфликтов"

        # Проверяем, что сотрудник появился в Ф2
        employee_in_f2 = self.get_employee_by_code(config.db_filial2, 1003)
        assert employee_in_f2 is not None, "Сотрудник должен быть в Ф2"
        assert employee_in_f2[2] == 'Козлов', "Фамилия должна совпадать"

    def test_02_employee_duplication_full_match(self):
        """Тест 2: Обработка полного дублирования сотрудников"""
        print("\n=== Тест 2: Обработка полного дублирования сотрудников ===")

        # ШАГ 1: Добавляем одинаковых сотрудников в оба филиала
        employee_data = {
            'EmplCode': 1004,
            'Name': 'Алексей',
            'Surname': 'Петров',
            'Patronymic': 'Сергеевич',
            'Birthday': date(1985, 10, 15),
            'Passport': '5555555555',
            'PosCode': 1,
            'Filial': 1
        }

        self.add_employee(config.db_filial1, employee_data)

        employee_data['Filial'] = 2
        self.add_employee(config.db_filial2, employee_data)

        print("Добавлены одинаковые сотрудники в оба филиала")

        # ШАГ 2: Эмуляция синхронизации
        self.emulate_sync()

        # ШАГ 3: Проверка отсутствия дублирования
        duplicate_count = self.check_duplicate_employees()
        conflict_count = self.get_conflict_count(config.db_filial1)

        print(f"Найдено дубликатов: {duplicate_count}")
        print(f"Количество конфликтов: {conflict_count}")

        assert duplicate_count == 0, "Не должно быть полных дубликатов"
        assert conflict_count == 0, "Не должно быть конфликтов при полном совпадении"

    def test_03_partial_match_conflict(self):
        """Тест 3: Обработка конфликта при частичном совпадении"""
        print("\n=== Тест 3: Обработка конфликта при частичном совпадении ===")

        # ШАГ 1: Добавляем сотрудников с частичным совпадением
        employee_f1 = {
            'EmplCode': 1005,
            'Name': 'Дмитрий',
            'Surname': 'Смирнов',
            'Patronymic': 'Викторович',
            'Birthday': date(1988, 3, 20),
            'Passport': '6666666666',
            'PosCode': 2,
            'Filial': 1
        }

        employee_f2 = {
            'EmplCode': 2005,
            'Name': 'Дмитрий',
            'Surname': 'Смирнов',
            'Patronymic': 'Викторович',
            'Birthday': date(1988, 3, 20),  # Совпадают ФИО и дата рождения
            'Passport': '7777777777',  # Но разный паспорт!
            'PosCode': 3,
            'Filial': 2
        }

        self.add_employee(config.db_filial1, employee_f1)
        self.add_employee(config.db_filial2, employee_f2)

        print("Добавлены сотрудники с частичным совпадением (разные паспорта)")

        # ШАГ 2: Эмуляция синхронизации
        self.emulate_sync()

        # ШАГ 3: Проверка конфликта
        conflict_count_f1 = self.get_conflict_count(config.db_filial1)
        conflict_count_f2 = self.get_conflict_count(config.db_filial2)

        print(f"Конфликтов в Ф1: {conflict_count_f1}")
        print(f"Конфликтов в Ф2: {conflict_count_f2}")

        assert conflict_count_f1 > 0 or conflict_count_f2 > 0, "Должен быть зафиксирован конфликт"

        # Проверяем, что данные не изменились
        employee1 = self.get_employee_by_code(config.db_filial1, 1005)
        employee2 = self.get_employee_by_code(config.db_filial2, 2005)

        assert employee1[5] == '6666666666', "Паспорт в Ф1 не должен измениться"
        assert employee2[5] == '7777777777', "Паспорт в Ф2 не должен измениться"

    def test_04_employment_history_sync(self):
        """Тест 4: Синхронизация истории трудоустройства"""
        print("\n=== Тест 4: Синхронизация истории трудоустройства ===")

        # ШАГ 1: Добавляем сотрудника и историю в Ф1
        employee_data = {
            'EmplCode': 1006,
            'Name': 'Ольга',
            'Surname': 'Иванова',
            'Patronymic': 'Петровна',
            'Birthday': date(1992, 7, 12),
            'Passport': '8888888888',
            'PosCode': 4,
            'Filial': 1
        }
        self.add_employee(config.db_filial1, employee_data)

        history_data = {
            'EmplCode': 1006,
            'ChangeDate': date.today(),
            'Surname': 'Иванова',
            'Passport': '8888888888',
            'PosCode': 4,
            'Action': 'Hired'
        }
        self.add_employment_history(config.db_filial1, history_data)

        initial_history_count = self.get_history_count(config.db_filial2, 1006)

        # ШАГ 2: Синхронизация
        self.emulate_sync()

        # ШАГ 3: Проверка синхронизации истории
        final_history_count = self.get_history_count(config.db_filial2, 1006)

        print(f"История до синхронизации: {initial_history_count}")
        print(f"История после синхронизации: {final_history_count}")

        assert final_history_count == initial_history_count + 1, "История должна синхронизироваться"

    def test_05_conflict_resolution(self):
        """Тест 5: Разрешение конфликта"""
        print("\n=== Тест 5: Разрешение конфликта ===")

        # Создаем конфликтную ситуацию
        self.test_03_partial_match_conflict()

        # ШАГ 1: Разрешаем конфликт (обновляем данные в Ф2)
        update_query = """
        UPDATE Employee 
        SET Passport = '6666666666'
        WHERE EmplCode = 2005
        """
        db_manager.execute_query(config.db_filial2, update_query)

        # Очищаем конфликты
        db_manager.execute_query(config.db_filial1, "DELETE FROM Conflist")
        db_manager.execute_query(config.db_filial2, "DELETE FROM Conflist")

        print("Конфликт разрешен вручную")

        # ШАГ 2: Повторная синхронизация
        self.emulate_sync()

        # ШАГ 3: Проверка
        conflict_count = self.get_conflict_count(config.db_filial1)
        duplicate_count = self.check_duplicate_employees()

        print(f"Конфликтов после разрешения: {conflict_count}")
        print(f"Дубликатов после разрешения: {duplicate_count}")

        assert conflict_count == 0, "После разрешения не должно быть конфликтов"
        assert duplicate_count == 0, "Не должно быть дубликатов"

    # Вспомогательные методы
    def emulate_sync(self):
        """Эмуляция процесса синхронизации"""
        # В реальной системе здесь будет вызов вашего job синхронизации
        # Для тестов просто делаем паузу
        import time
        time.sleep(1)
        print("Синхронизация выполнена")

    def get_employee_by_code(self, database: str, empl_code: int):
        """Получить сотрудника по коду"""
        query = "SELECT * FROM Employee WHERE EmplCode = %s"
        result = db_manager.execute_query(database, query, (empl_code,), fetch=True)
        return result[0] if result else None

    def get_history_count(self, database: str, empl_code: int):
        """Получить количество записей в истории для сотрудника"""
        query = "SELECT COUNT(*) FROM EmplHistory WHERE EmplCode = %s"
        return db_manager.execute_query(database, query, (empl_code,), fetch=True)[0][0]

    def check_duplicate_employees(self):
        """Проверить наличие дубликатов сотрудников"""
        query = """
        SELECT COUNT(*) FROM (
            SELECT Surname, Name, Patronymic, Birthday, Passport, COUNT(*)
            FROM Employee
            GROUP BY Surname, Name, Patronymic, Birthday, Passport
            HAVING COUNT(*) > 1
        ) AS duplicates
        """
        result1 = db_manager.execute_query(config.db_filial1, query, fetch=True)[0][0]
        result2 = db_manager.execute_query(config.db_filial2, query, fetch=True)[0][0]
        return result1 + result2