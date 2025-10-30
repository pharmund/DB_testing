import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import urllib.parse

load_dotenv()


class Config:
    # Данные подключения к базам
    DB_FILIAL1 = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': 'filial1',
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }

    DB_FILIAL2 = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': 'filial2',
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }

    # Генерация URL для SQLAlchemy
    @classmethod
    def get_db_url(cls, db_config):
        # Экранируем специальные символы в пароле
        password = urllib.parse.quote_plus(db_config['password'])
        return f"postgresql://{db_config['user']}:{password}@{db_config['host']}:{db_config['port']}/{db_config['database']}"


class TestConfig:
    # Тестовые данные
    TEST_EMPLOYEE_BASE_CODE = 6000  # Начальный код для тестовых сотрудников

    @classmethod
    def get_test_passport(cls, test_number):
        return f'600{test_number}600{test_number}0'