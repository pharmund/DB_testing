# Тестирование синхронизации баз данных филиалов

## 🎯 Общее описание проекта

Проект предназначен для тестирования механизма синхронизации данных между базами данных двух филиалов компании, расположенных в разных городах России. Каждый филиал использует отдельный экземпляр ИС с собственной БД.

**Основная задача**: Проверить корректность работы процедур синхронизации по всем изменениям на полноту, непротиворечивость, отсутствие дублирования информации.

---

## 🧪 Два подхода к тестированию

### 1. **Python-тесты** (автоматизированные)

- Запускаются через pytest
    
- Используют SQLAlchemy для работы с БД
    
- Автоматическая очистка данных
    
- Детальное логирование
    

### 2. **SQL-тесты** (прямые в БД)

- Запускаются через pgAdmin или DBeaver
    
- Написаны на чистом SQL/PLpgSQL
    
- Позволяют тестировать логику напрямую в БД
    
- Идеальны для отладки и демонстрации
    

---

## 📋 Тестовые сценарии

### 🔄 1. Синхронизация нового сотрудника

**Цель**: Нанятый сотрудник в Ф1 после синхронизации доступен и в Ф2

### 📝 2. Синхронизация увольнения

**Цель**: Уволенный сотрудник в Ф2 после синхронизации уволен и в Ф1

### 🔍 3. Предотвращение дублирования

**Цель**: При одновременном оформлении сотрудников в двух филиалах с совпадающими ФИО, датой рождения и номером паспорта не происходит дублирования

### ⚠️ 4. Обработка конфликтов

**Цель**: При совпадении 2 из 3 ключевых параметров синхронизация не производится, информация поступает в Журнал конфликтов

### ✅ 5. Разрешение конфликтов

**Цель**: После разрешения конфликта экспертами происходит синхронизация согласно принятому решению, запись из журнала удаляется

### 📊 6. Сохранение истории изменений

**Цель**: При изменении информации о сотруднике не происходит нарушения истории изменений

---

## 🗄️ Структура базы данных

### Таблица `Employee`

|Поле|Тип|Ограничения|Описание|
|---|---|---|---|
|EmplCode|Integer|Not NULL, PK|Табельный номер сотрудника|
|Name|Varchar(50)|Not NULL|Имя сотрудника|
|Surname|Varchar(50)|Not NULL|Фамилия сотрудника|
|Patronymic|Varchar(50)|Not NULL|Отчество сотрудника|
|Birthday|Date|Not NULL|Дата рождения|
|Passport|Varchar(10)|Not NULL|Паспорт|
|PosCode|Integer|Not NULL, FK|Должность|
|Filial|Integer|Not NULL|Принадлежность филиалу|
|Status|Varchar(20)|DEFAULT 'Active'|Статус сотрудника|

### Таблица `Positions`

|Поле|Тип|Ограничения|Описание|
|---|---|---|---|
|PosCode|Integer|Not NULL, PK|Код должности|
|PosName|Varchar(100)|Not NULL|Наименование должности|
|ParentPos|Integer|Nullable|Подчиненность должности|
|Filial|Integer|Not NULL|Принадлежность филиалу|

### Таблица `EmplHistory`

|Поле|Тип|Ограничения|Описание|
|---|---|---|---|
|EmplCode|Integer|Not NULL, FK|Табельный номер сотрудника|
|ChangeDate|Date|Not NULL|Дата изменения|
|Surname|Varchar(50)|Not NULL|Фамилия сотрудника|
|Passport|Varchar(10)|Not NULL|Паспорт|
|PosCode|Integer|Not NULL, FK|Должность|

### Таблица `Conflist`

|Поле|Тип|Ограничения|Описание|
|---|---|---|---|
|EmplCode|Integer|Not NULL, FK|Табельный номер сотрудника|
|Errlist|Varchar(1000)|Not NULL|Описание ошибки синхронизации|

---

## ⚡ БЫСТРЫЙ СТАРТ: Запуск SQL-тестов

### Шаг 1: Установка PostgreSQL

Следуйте инструкциям в разделе "Установка и настройка PostgreSQL" ниже.

### Шаг 2: Создание структуры БД

Выполните SQL-скрипты создания базы данных и таблиц из раздела "Создание баз данных и таблиц".

### Шаг 3: Запуск SQL-тестов

#### Вариант A: Через pgAdmin

1. Откройте pgAdmin 4
    
2. Подключитесь к вашей БД PostgreSQL
    
3. Откройте Query Tool
    
4. Вставьте содержимое файла `sql_tests.sql`
    
5. Выполните весь скрипт (F5)
    

#### Вариант B: Через DBeaver

1. Откройте DBeaver
    
2. Подключитесь к БД
    
3. Создайте новый SQL-скрипт
    
4. Вставьте код тестов
    
5. Выполните скрипт (Ctrl+Enter)
    

### Шаг 4: Запуск отдельных тестов

sql

-- Запуск всех тестов сразу
SELECT * FROM run_all_tests();

-- Запуск отдельных тестов
SELECT * FROM test_1_new_employee_sync();
SELECT * FROM test_2_employee_dismissal_sync();
SELECT * FROM test_3_duplicate_prevention();
SELECT * FROM test_4_partial_match_conflict();
SELECT * FROM test_5_conflict_resolution();
SELECT * FROM test_6_change_history_preservation();

-- Очистка тестовых данных
SELECT cleanup_test_data();

-- Просмотр состояния БД
SELECT * FROM make_data_snapshot();

---

## 🏗️ Архитектура SQL-тестов

### Вспомогательные функции:

#### `make_data_snapshot()`

- Создает снимок текущего состояния БД
    
- Показывает количество записей в каждой таблице
    

#### `emulate_synchronization()`

- Эмулирует процесс синхронизации между филиалами
    
- Переносит новых сотрудников между БД
    
- Обновляет статусы уволенных сотрудников
    
- Обнаруживает и регистрирует конфликты
    

#### `resolve_conflict(conflict_id, resolution_action)`

- Разрешает конфликты тремя способами:
    
    - `MERGE` - объединить записи
        
    - `KEEP_BOTH` - сохранить обе записи
        
    - `UPDATE_DATA` - обновить данные
        

#### `cleanup_test_data()`

- Очищает тестовые данные (EmplCode >= 5000)
    

---

## 📊 Детальное описание SQL-тестов

### 🧪 ТЕСТ 1: `test_1_new_employee_sync()`

**Цель**: Проверить синхронизацию нового сотрудника из Ф1 в Ф2

sql

Шаги:
1. Добавляем сотрудника в Ф1 с паспортом '5001500150'
2. Запускаем emulate_synchronization()
3. Проверяем наличие сотрудника в Ф2 по паспорту

**Механизм**:

sql

INSERT INTO Employee (Ф2)
SELECT ... FROM Employee 
WHERE Filial = 1 
AND Passport NOT IN (SELECT Passport FROM Employee WHERE Filial = 2)

### 🧪 ТЕСТ 2: `test_2_employee_dismissal_sync()`

**Цель**: Проверить синхронизацию увольнения

sql

Шаги:
1. Создаем одинакового сотрудника в обоих филиалах
2. Увольняем в Ф2 (Status = 'Fired')
3. Синхронизируем
4. Проверяем статус в Ф1

**Механизм**:

sql

UPDATE Employee e1
SET Status = 'Fired'
FROM Employee e2
WHERE e1.Passport = e2.Passport 
AND e1.Filial != e2.Filial 
AND e2.Status = 'Fired'

### 🧪 ТЕСТ 3: `test_3_duplicate_prevention()`

**Цель**: Обнаружение конфликтов при полном совпадении данных

sql

Шаги:
1. Создаем сотрудников с одинаковыми ФИО, датой рождения и паспортом
2. Синхронизируем
3. Проверяем регистрацию конфликта в Conflist

**Критерий конфликта**: Одинаковые паспортные данные

### 🧪 ТЕСТ 4: `test_4_partial_match_conflict()`

**Цель**: Обнаружение конфликтов при частичном совпадении

sql

Шаги:
1. Создаем сотрудников с одинаковыми ФИО и датой рождения
2. Но с РАЗНЫМИ паспортами
3. Синхронизируем
4. Проверяем обнаружение конфликта

**Критерий**: Совпадение ФИО + даты рождения

### 🧪 ТЕСТ 5: `test_5_conflict_resolution()`

**Цель**: Проверить процесс разрешения конфликтов

sql

Шаги:
1. Создаем конфликтную ситуацию
2. Регистрируем конфликт
3. Разрешаем через resolve_conflict()
4. Проверяем пометку Resolved = TRUE

**Стратегии разрешения**: MERGE, KEEP_BOTH, UPDATE_DATA

### 🧪 ТЕСТ 6: `test_6_change_history_preservation()`

**Цель**: Сохранение истории изменений

sql

Шаги:
1. Создаем сотрудника
2. Вносим изменения в данные
3. Добавляем запись в EmplHistory
4. Синхронизируем
5. Проверяем сохранение истории

---

## 🚀 Запуск Python-тестов

### 1. Установка зависимостей Python

bash

pip install -r requirements.txt

### 2. Настройка подключения к БД

Создайте файл `.env` в корне проекта:

env

DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password

### 3. Запуск тестов

**Рекомендуемая последовательность:**

bash

### Принудительная очистка баз данных от тестовых данных
python cleanup_databases.py

### Диагностика состояния баз данных
python debug_database.py

### Запуск всех тестов
python run_tests.py

**Альтернативные способы запуска:**

bash

### Запуск через pytest с детализацией
pytest test_synchronization.py -v

### Запуск с генерацией отчета
pytest test_synchronization.py --html=report.html

### Запуск конкретного теста
pytest test_synchronization.py::TestSynchronization::test_1_new_employee_sync -v

---

## ⚙️ Установка и настройка PostgreSQL

### 📥 Скачивание и установка

1. **Перейдите на официальный сайт**: [postgresql.org/download](https://www.postgresql.org/download/)
    
2. **Выберите вашу ОС** и скачайте установщик
    

### 🪟 Установка на Windows

1. **Запустите установщик** и нажмите "Next"
    
2. **Выберите компоненты**:
    
    text
    
    ☑ PostgreSQL Server
    ☑ pgAdmin 4 (графический интерфейс)
    ☑ Command Line Tools
    
3. **Укажите директорию установки**: `C:\Program Files\PostgreSQL\16\`
    
4. **Задайте пароль для пользователя `postgres`** (запомните его!)
    
5. **Оставьте порт по умолчанию**: `5432`
    
6. **Завершите установку**
    

### 🛠️ Создание баз данных и таблиц

#### 1. Подключитесь к СУБД через DBeaver или pgAdmin 4

#### 2. Создайте базы данных:

sql

-- Создание базы для филиала 1
CREATE DATABASE filial1
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- Создание базы для филиала 2  
CREATE DATABASE filial2
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

#### 3. Выполните в обеих базах следующую структуру:

sql

-- Таблица должностей
CREATE TABLE Positions (
    PosCode INTEGER NOT NULL PRIMARY KEY,
    PosName VARCHAR(100) NOT NULL,
    ParentPos INTEGER NULL,
    Filial INTEGER NOT NULL
);

-- Таблица сотрудников
CREATE TABLE Employee (
    EmplCode INTEGER NOT NULL PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Surname VARCHAR(50) NOT NULL,
    Patronymic VARCHAR(50) NOT NULL,
    Birthday DATE NOT NULL,
    Passport VARCHAR(10) NOT NULL,
    PosCode INTEGER NOT NULL,
    Filial INTEGER NOT NULL,
    Status VARCHAR(20) DEFAULT 'Active',
    FOREIGN KEY (PosCode) REFERENCES Positions(PosCode)
);

-- Таблица истории изменений
CREATE TABLE EmplHistory (
    HistoryID SERIAL PRIMARY KEY,
    EmplCode INTEGER NOT NULL,
    ChangeDate DATE NOT NULL,
    Surname VARCHAR(50) NOT NULL,
    Passport VARCHAR(10) NOT NULL,
    PosCode INTEGER NOT NULL,
    Action VARCHAR(50) NOT NULL,
    FOREIGN KEY (EmplCode) REFERENCES Employee(EmplCode),
    FOREIGN KEY (PosCode) REFERENCES Positions(PosCode)
);

-- Таблица конфликтов
CREATE TABLE Conflist (
    ConflictID SERIAL PRIMARY KEY,
    EmplCode INTEGER NOT NULL,
    Errlist VARCHAR(1000) NOT NULL,
    ConflictDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Resolved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (EmplCode) REFERENCES Employee(EmplCode)
);

#### 4. Заполните тестовыми данными (в обеих базах):

sql

-- Общие должности
INSERT INTO Positions (PosCode, PosName, ParentPos, Filial) VALUES
(1, 'Менеджер', NULL, 1),
(2, 'Разработчик', NULL, 1),
(3, 'Аналитик', NULL, 2),
(4, 'Дизайнер', NULL, 2);

-- Начальные сотрудники для Ф1
INSERT INTO Employee (EmplCode, Name, Surname, Patronymic, Birthday, Passport, PosCode, Filial) VALUES
(1001, 'Иван', 'Иванов', 'Иванович', '1990-01-01', '1234567890', 1, 1),
(1002, 'Петр', 'Петров', 'Петрович', '1991-02-02', '1111111111', 2, 1);

-- Начальные сотрудники для Ф2  
INSERT INTO Employee (EmplCode, Name, Surname, Patronymic, Birthday, Passport, PosCode, Filial) VALUES
(2001, 'Мария', 'Сидорова', 'Ивановна', '1992-03-03', '2222222222', 3, 2),
(2002, 'Анна', 'Смирнова', 'Петровна', '1993-04-04', '3333333333', 4, 2);

---

## 📁 Структура проекта

text

tests/
├── config.py              # Конфигурация подключения к БД
├── models.py              # SQLAlchemy модели данных
├── database.py            # Менеджер работы с базами данных
├── test_base.py           # Базовый класс для тестов
├── test_synchronization.py # Основные тесты синхронизации
├── run_tests.py           # Главный скрипт запуска тестов
├── cleanup_databases.py   # Скрипт принудительной очистки БД
├── debug_database.py      # Скрипт диагностики состояния БД
├── sql_tests.sql          # SQL-версия тестов для pgAdmin
└── requirements.txt       # Зависимости проекта

---

## 🎯 Ключевые особенности реализации

### 🛡️ Изоляция тестов

- Каждый тест запускается в чистом окружении
    
- Автоматическая генерация уникальных тестовых данных (EmplCode >= 5000)
    
- Предотвращение конфликтов между параллельными запусками
    

### 🔄 Двусторонняя синхронизация

sql

-- Из Ф1 → Ф2
INSERT INTO Employee (Ф2) SELECT ... FROM Employee WHERE Filial = 1

-- Из Ф2 → Ф1  
INSERT INTO Employee (Ф1) SELECT ... FROM Employee WHERE Filial = 2

### ⚠️ Многоуровневое обнаружение конфликтов

- **Полное совпадение**: одинаковые паспорта
    
- **Частичное совпадение**: одинаковые ФИО + дата рождения
    

### 🧹 Автоматическая очистка

sql

SELECT cleanup_test_data();  -- Очистка тестовых данных

---

## 🔧 Утилиты

### SQL-функции:

- `make_data_snapshot()` - диагностика состояния БД
    
- `cleanup_test_data()` - очистка тестовых данных
    
- `emulate_synchronization()` - эмуляция процесса синхронизации
    

### Python-скрипты:

- `cleanup_databases.py` - полная очистка тестовых данных
    
- `debug_database.py` - диагностика состояния баз данных
    

---

## 📊 Логирование и результаты

### SQL-тесты:

- Результаты возвращаются в виде таблицы
    
- Детальное описание каждого шага
    
- Временные метки выполнения
    

### Python-тесты:

- `test_results_YYYYMMDD_HHMMSS.log` - детальные логи
    
- Консольный вывод с цветовым оформлением
    
- HTML-отчеты при использовании pytest-html
    

---

## 🐛 Решение проблем

### Если SQL-тесты не работают:

1. Проверьте, что функции созданы в правильной БД
    
2. Убедитесь, что выполнены все скрипты создания структуры
    
3. Проверьте права доступа пользователя
    

### Если Python-тесты не проходят:

1. Запустите принудительную очистку: `python cleanup_databases.py`
    
2. Проверьте подключение к БД: `python debug_database.py`
    
3. Убедитесь, что базы данных запущены и доступны
    

### Если возникают ошибки подключения:

1. Проверьте настройки в `.env` файле
    
2. Убедитесь, что PostgreSQL запущен
    
3. Проверьте корректность имени пользователя и пароля
    

---

## 📞 Поддержка

При возникновении вопросов:

1. Для SQL-тестов - проверьте синтаксис в pgAdmin
    
2. Для Python-тестов - проверьте логи в папке проекта
    
3. Убедитесь, что все зависимости установлены
    

---

## 🔒 Требования к окружению

- Python 3.8+
    
- PostgreSQL 12+
    
- Доступ к двум базам данных: `filial1` и `filial2`
    
- pgAdmin 4 или DBeaver для работы с SQL-тестами
    

Теперь у вас есть полная картина тестирования системы синхронизации с двумя подходами: автоматизированным (Python) и прямым (SQL)!