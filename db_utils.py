from config import db_manager, config


def initialize_test_data():
    """Инициализация тестовых данных в обеих базах"""

    # Очистка старых данных
    cleanup_queries = [
        "DELETE FROM Conflist",
        "DELETE FROM EmplHistory",
        "DELETE FROM Employee",
        "DELETE FROM Positions"
    ]

    for db in [config.db_filial1, config.db_filial2]:
        for query in cleanup_queries:
            try:
                db_manager.execute_query(db, query)
            except Exception as e:
                print(f"Warning during cleanup: {e}")

    # Добавление тестовых должностей
    positions = [
        (1, 'Менеджер', None, 1),
        (2, 'Разработчик', None, 1),
        (3, 'Аналитик', None, 2),
        (4, 'Дизайнер', None, 2)
    ]

    for db in [config.db_filial1, config.db_filial2]:
        for pos in positions:
            query = "INSERT INTO Positions (PosCode, PosName, ParentPos, Filial) VALUES (%s, %s, %s, %s)"
            db_manager.execute_query(db, query, pos)

    # Добавление тестовых сотрудников
    employees_f1 = [
        (1001, 'Иван', 'Иванов', 'Иванович', '1990-01-01', '1234567890', 1, 1),
        (1002, 'Петр', 'Петров', 'Петрович', '1991-02-02', '1111111111', 2, 1)
    ]

    employees_f2 = [
        (2001, 'Мария', 'Сидорова', 'Ивановна', '1992-03-03', '2222222222', 3, 2),
        (2002, 'Анна', 'Смирнова', 'Петровна', '1993-04-04', '3333333333', 4, 2)
    ]

    for emp in employees_f1:
        query = """
        INSERT INTO Employee (EmplCode, Name, Surname, Patronymic, Birthday, Passport, PosCode, Filial)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        db_manager.execute_query(config.db_filial1, query, emp)

    for emp in employees_f2:
        query = """
        INSERT INTO Employee (EmplCode, Name, Surname, Patronymic, Birthday, Passport, PosCode, Filial)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        db_manager.execute_query(config.db_filial2, query, emp)

    print("✅ Тестовые данные инициализированы в обеих базах")


def check_database_health():
    """Проверка состояния баз данных"""
    print("\n=== Проверка состояния баз данных ===")

    for db_name in [config.db_filial1, config.db_filial2]:
        try:
            # Проверяем подключение
            conn = db_manager.get_connection(db_name)

            # Проверяем основные таблицы
            tables = ['Employee', 'Positions', 'EmplHistory', 'Conflist']
            for table in tables:
                query = f"SELECT COUNT(*) FROM {table}"
                count = db_manager.execute_query(db_name, query, fetch=True)[0][0]
                print(f"📊 {db_name}.{table}: {count} записей")

            conn.close()
            print(f"✅ База {db_name} в порядке")

        except Exception as e:
            print(f"❌ Ошибка при проверке {db_name}: {e}")


if __name__ == "__main__":
    initialize_test_data()
    check_database_health()