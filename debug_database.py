from database import DatabaseManager
from sqlalchemy import text


def check_database_state():
    """Проверка состояния базы данных"""
    db = DatabaseManager()

    try:
        print("=== ДИАГНОСТИКА БАЗ ДАННЫХ ===")

        for db_name in ['filial1', 'filial2']:
            session = db.get_session(db_name)
            try:
                # Общее количество сотрудников
                total_count = session.execute(text("SELECT COUNT(*) FROM employee")).scalar()

                # Количество по филиалам
                filial_1_count = session.execute(
                    text("SELECT COUNT(*) FROM employee WHERE filial = 1")
                ).scalar()
                filial_2_count = session.execute(
                    text("SELECT COUNT(*) FROM employee WHERE filial = 2")
                ).scalar()

                # Тестовые данные
                test_count = session.execute(
                    text("SELECT COUNT(*) FROM employee WHERE passport LIKE '600%600%0'")
                ).scalar()

                print(f"\n{db_name.upper()}:")
                print(f"  Всего сотрудников: {total_count}")
                print(f"  Филиал 1: {filial_1_count}")
                print(f"  Филиал 2: {filial_2_count}")
                print(f"  Тестовых записей: {test_count}")

                if test_count > 0:
                    test_employees = session.execute(
                        text("SELECT emplcode, passport, filial FROM employee WHERE passport LIKE '600%600%0'")
                    ).fetchall()
                    print(f"  Тестовые сотрудники: {test_employees}")

            finally:
                session.close()

    finally:
        db.close()


if __name__ == "__main__":
    check_database_state()