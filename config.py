import psycopg2
from dataclasses import dataclass


@dataclass
class DBConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "your_password"

    db_filial1: str = "filial1"
    db_filial2: str = "filial2"


class DatabaseManager:
    def __init__(self, config: DBConfig):
        self.config = config

    def get_connection(self, database: str):
        return psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=database
        )

    def execute_query(self, database: str, query: str, params=None, fetch=False):
        conn = self.get_connection(database)
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                conn.commit()
                return cursor.rowcount
        finally:
            conn.close()


# Конфигурация
config = DBConfig()
db_manager = DatabaseManager(config)