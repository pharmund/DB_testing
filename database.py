from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import Config
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.engines = {}
        self.sessions = {}
        self._setup_databases()

    def _setup_databases(self):
        """Настройка подключений к обеим базам"""
        databases = {
            'filial1': Config.get_db_url(Config.DB_FILIAL1),
            'filial2': Config.get_db_url(Config.DB_FILIAL2)
        }

        for name, url in databases.items():
            try:
                engine = create_engine(url)

                # Тестируем подключение
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                self.engines[name] = engine
                self.sessions[name] = sessionmaker(bind=engine)
                logger.info(f"Успешное подключение к {name}")

            except Exception as e:
                logger.error(f"Ошибка подключения к {name}: {e}")
                raise

    def get_session(self, database_name):
        """Получить сессию для указанной базы"""
        if database_name not in self.sessions:
            raise ValueError(f"База данных {database_name} не настроена")
        return self.sessions[database_name]()

    def execute_function(self, database_name, function_name, *args):
        """Выполнить функцию в базе данных"""
        session = self.get_session(database_name)
        try:
            if args:
                result = session.execute(text(f"SELECT {function_name}({','.join(['%s'] * len(args))})"), args)
            else:
                result = session.execute(text(f"SELECT {function_name}()"))

            return result.fetchall()
        finally:
            session.close()

    def safe_synchronize_employee(self, source_db, target_db, passport):
        """Безопасная синхронизация сотрудника по паспорту - только если его нет в целевой базе"""
        source_session = self.get_session(source_db)
        target_session = self.get_session(target_db)

        try:
            # Определяем целевой филиал для более точной проверки
            target_filial = 2 if target_db == 'filial2' else 1

            # Проверяем, есть ли уже сотрудник в целевой базе с таким паспортом И филиалом
            target_exists = target_session.execute(
                text("SELECT COUNT(*) FROM employee WHERE passport = :passport AND filial = :filial"),
                {'passport': passport, 'filial': target_filial}
            ).scalar()

            if target_exists > 0:
                logger.info(f"Сотрудник с паспортом {passport} уже существует в {target_db} (филиал {target_filial})")
                return False

            # Получаем данные сотрудника из source базы
            source_filial = 1 if source_db == 'filial1' else 2
            employee_data = source_session.execute(
                text("""
                    SELECT name, surname, patronymic, birthday, passport, poscode, status
                    FROM employee 
                    WHERE passport = :passport AND filial = :filial AND status = 'Active'
                """),
                {'passport': passport, 'filial': source_filial}
            ).fetchone()

            if not employee_data:
                logger.warning(
                    f"Активный сотрудник с паспортом {passport} не найден в {source_db} (филиал {source_filial})")
                return False

            # Генерируем новый emplcode для целевой базы
            max_code_result = target_session.execute(
                text("SELECT COALESCE(MAX(emplcode), 0) FROM employee")
            )
            new_emplcode = max_code_result.scalar() + 1

            # Вставляем сотрудника в целевую базу
            target_session.execute(
                text("""
                    INSERT INTO employee (emplcode, name, surname, patronymic, birthday, passport, poscode, filial, status)
                    VALUES (:emplcode, :name, :surname, :patronymic, :birthday, :passport, :poscode, :filial, :status)
                """),
                {
                    'emplcode': new_emplcode,
                    'name': employee_data.name,
                    'surname': employee_data.surname,
                    'patronymic': employee_data.patronymic,
                    'birthday': employee_data.birthday,
                    'passport': employee_data.passport,
                    'poscode': employee_data.poscode,
                    'filial': target_filial,
                    'status': employee_data.status
                }
            )

            target_session.commit()
            logger.info(f"Сотрудник {passport} синхронизирован из {source_db} в {target_db} с кодом {new_emplcode}")
            return True

        except Exception as e:
            target_session.rollback()
            logger.error(f"Ошибка синхронизации сотрудника {passport}: {e}")
            return False
        finally:
            source_session.close()
            target_session.close()

    def safe_synchronize_dismissal(self, source_db, target_db, passport):
        """Безопасная синхронизация увольнения"""
        source_session = self.get_session(source_db)
        target_session = self.get_session(target_db)

        try:
            # Получаем статус из source базы
            status_result = source_session.execute(
                text("SELECT status FROM employee WHERE passport = :passport"),
                {'passport': passport}
            )

            source_status = status_result.scalar()

            if not source_status:
                logger.warning(f"Сотрудник с паспортом {passport} не найден в {source_db}")
                return False

            # Обновляем статус в целевой базе
            result = target_session.execute(
                text("UPDATE employee SET status = :status WHERE passport = :passport"),
                {'status': source_status, 'passport': passport}
            )

            updated_count = result.rowcount
            target_session.commit()

            if updated_count > 0:
                logger.info(f"Статус сотрудника {passport} обновлен в {target_db}: {source_status}")
                return True
            else:
                logger.warning(f"Сотрудник с паспортом {passport} не найден в {target_db} для обновления статуса")
                return False

        except Exception as e:
            target_session.rollback()
            logger.error(f"Ошибка синхронизации увольнения для {passport}: {e}")
            return False
        finally:
            source_session.close()
            target_session.close()

    def cleanup_test_data(self):
        """Очистка тестовых данных в обеих базах"""
        for db_name in ['filial1', 'filial2']:
            session = self.get_session(db_name)
            try:
                # Сначала удаляем данные из зависимых таблиц по emplcode
                session.execute(text("""
                    DELETE FROM conflist 
                    WHERE emplcode >= 5000 
                    OR errlist LIKE '%TEST%'
                """))

                session.execute(text("""
                    DELETE FROM emplhistory 
                    WHERE emplcode >= 5000 
                """))

                # Затем удаляем сотрудников
                session.execute(text("""
                    DELETE FROM employee 
                    WHERE emplcode >= 5000 
                    OR passport LIKE '600%600%0'
                """))

                session.commit()
                logger.info(f"Тестовые данные очищены в {db_name}")

                # Проверяем, что данные действительно удалены
                remaining_count = session.execute(
                    text("SELECT COUNT(*) FROM employee WHERE emplcode >= 5000 OR passport LIKE '600%600%0'")
                ).scalar()

                if remaining_count > 0:
                    logger.warning(f"В {db_name} осталось {remaining_count} тестовых записей")

            except Exception as e:
                session.rollback()
                logger.error(f"Ошибка при очистке данных в {db_name}: {e}")
                # Не прерываем выполнение, просто логируем ошибку
            finally:
                session.close()

    def close(self):
        """Закрыть все соединения"""
        for engine in self.engines.values():
            engine.dispose()