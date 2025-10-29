import pytest
from config import db_manager, config


class BaseSyncTest:
    """Базовый класс для всех тестов синхронизации"""

    def setup_method(self):
        """Очистка данных перед каждым тестом"""
        self.clean_test_data()

    def clean_test_data(self):
        """Очистка тестовых данных в обеих базах"""
        clean_queries = [
            "DELETE FROM Conflist",
            "DELETE FROM EmplHistory",
            "DELETE FROM Employee WHERE EmplCode >= 1000",
            "DELETE FROM Positions WHERE PosCode >= 100"
        ]

        for db in [config.db_filial1, config.db_filial2]:
            for query in clean_queries:
                try:
                    db_manager.execute_query(db, query)
                except Exception as e:
                    print(f"Warning: {e}")

    def make_snapshot(self, database: str):
        """Создание снимка данных"""
        query = "SELECT * FROM make_data_snapshot()"
        return db_manager.execute_query(database, query, fetch=True)

    def get_employee_count(self, database: str, filial: int = None):
        """Получить количество сотрудников"""
        if filial:
            query = "SELECT COUNT(*) FROM Employee WHERE Filial = %s"
            return db_manager.execute_query(database, query, (filial,), fetch=True)[0][0]
        else:
            query = "SELECT COUNT(*) FROM Employee"
            return db_manager.execute_query(database, query, fetch=True)[0][0]

    def get_conflict_count(self, database: str):
        """Получить количество конфликтов"""
        query = "SELECT COUNT(*) FROM Conflist"
        return db_manager.execute_query(database, query, fetch=True)[0][0]

    def add_employee(self, database: str, employee_data: dict):
        """Добавить сотрудника"""
        query = """
        INSERT INTO Employee (EmplCode, Name, Surname, Patronymic, Birthday, Passport, PosCode, Filial)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return db_manager.execute_query(database, query, tuple(employee_data.values()))

    def add_position(self, database: str, position_data: dict):
        """Добавить должность"""
        query = """
        INSERT INTO Positions (PosCode, PosName, ParentPos, Filial)
        VALUES (%s, %s, %s, %s)
        """
        return db_manager.execute_query(database, query, tuple(position_data.values()))

    def add_employment_history(self, database: str, history_data: dict):
        """Добавить запись в историю"""
        query = """
        INSERT INTO EmplHistory (EmplCode, ChangeDate, Surname, Passport, PosCode, Action)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        return db_manager.execute_query(database, query, tuple(history_data.values()))