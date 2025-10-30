#!/usr/bin/env python3
from database import DatabaseManager
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def force_cleanup_databases():
    """Принудительная очистка тестовых данных в обеих базах"""
    db = DatabaseManager()

    try:
        for db_name in ['filial1', 'filial2']:
            session = db.get_session(db_name)
            try:
                # Полная очистка тестовых данных
                session.execute(text("DELETE FROM conflist WHERE emplcode >= 5000 OR errlist LIKE '%TEST%'"))
                session.execute(text("DELETE FROM emplhistory WHERE emplcode >= 5000"))
                session.execute(text("DELETE FROM employee WHERE emplcode >= 5000 OR passport LIKE '600%600%0'"))

                session.commit()
                logger.info(f"✅ База {db_name} полностью очищена от тестовых данных")

                # Проверяем результат
                remaining = session.execute(
                    text("SELECT COUNT(*) FROM employee WHERE emplcode >= 5000 OR passport LIKE '600%600%0'")
                ).scalar()

                if remaining == 0:
                    logger.info(f"✅ В {db_name} нет тестовых данных")
                else:
                    logger.warning(f"⚠️ В {db_name} осталось {remaining} тестовых записей")

            except Exception as e:
                session.rollback()
                logger.error(f"❌ Ошибка при очистке {db_name}: {e}")
            finally:
                session.close()

    finally:
        db.close()


if __name__ == "__main__":
    print("=== ПРИНУДИТЕЛЬНАЯ ОЧИСТКА БАЗ ДАННЫХ ===")
    force_cleanup_databases()