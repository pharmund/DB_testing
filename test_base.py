import pytest
from database import DatabaseManager
import logging
from sqlalchemy import text
import time

logger = logging.getLogger(__name__)


class TestBase:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Настройка перед каждым тестом"""
        self.db = DatabaseManager()
        self.test_counter = int(time.time() % 10000)  # Уникальный базовый номер
        yield
        # Очистка после каждого теста
        try:
            self.db.cleanup_test_data()
        except Exception as e:
            logger.warning(f"Ошибка при очистке тестовых данных: {e}")
        finally:
            self.db.close()

    def get_next_test_code(self):
        """Генерация следующего тестового кода сотрудника"""
        self.test_counter += 1
        return 6000 + self.test_counter

    def get_test_passport(self, test_number):
        """Генерация тестового паспорта с временной меткой для уникальности"""
        timestamp = int(time.time() % 10000)
        return f'7{timestamp:04d}{test_number:02d}0'

    def emulate_synchronization(self):
        """Эмуляция синхронизации между филиалами - безопасная версия"""
        logger = logging.getLogger(__name__)
        logger.info("Используется безопасная эмуляция синхронизации")
        return True, True

    def safe_sync_new_employee(self, passport):
        """Безопасная синхронизация НОВОГО сотрудника - только из Ф1 в Ф2"""
        # Только односторонняя синхронизация: из Ф1 в Ф2
        result = self.db.safe_synchronize_employee('filial1', 'filial2', passport)
        return result

    def safe_sync_dismissal(self, passport):
        """Безопасная синхронизация увольнения - двусторонняя"""
        # Синхронизируем статус из Ф2 в Ф1
        result1 = self.db.safe_synchronize_dismissal('filial2', 'filial1', passport)
        # Синхронизируем статус из Ф1 в Ф2 (на случай изменений в Ф1)
        result2 = self.db.safe_synchronize_dismissal('filial1', 'filial2', passport)
        return result1, result2

    def get_employee_count(self, database_name, filial=None):
        """Получить количество сотрудников в указанной базе"""
        session = self.db.get_session(database_name)
        try:
            if filial:
                result = session.execute(
                    text("SELECT COUNT(*) FROM employee WHERE filial = :filial"),
                    {'filial': filial}
                )
            else:
                result = session.execute(text("SELECT COUNT(*) FROM employee"))
            return result.scalar()
        finally:
            session.close()

    def get_conflict_count(self, database_name, resolved=None):
        """Получить количество конфликтов"""
        session = self.db.get_session(database_name)
        try:
            if resolved is not None:
                result = session.execute(
                    text("SELECT COUNT(*) FROM conflist WHERE resolved = :resolved"),
                    {'resolved': resolved}
                )
            else:
                result = session.execute(text("SELECT COUNT(*) FROM conflist"))
            return result.scalar()
        finally:
            session.close()

    def employee_exists(self, database_name, passport, filial=None):
        """Проверить существование сотрудника по паспорту"""
        session = self.db.get_session(database_name)
        try:
            if filial:
                result = session.execute(
                    text("SELECT COUNT(*) FROM employee WHERE passport = :passport AND filial = :filial"),
                    {'passport': passport, 'filial': filial}
                )
            else:
                result = session.execute(
                    text("SELECT COUNT(*) FROM employee WHERE passport = :passport"),
                    {'passport': passport}
                )
            return result.scalar() > 0
        finally:
            session.close()

    def add_employee(self, database_name, empl_data):
        """Добавить сотрудника в указанную базу"""
        session = self.db.get_session(database_name)
        try:
            session.execute(
                text("""
                    INSERT INTO employee (emplcode, name, surname, patronymic, birthday, passport, poscode, filial, status)
                    VALUES (:emplcode, :name, :surname, :patronymic, :birthday, :passport, :poscode, :filial, :status)
                """),
                empl_data
            )
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()