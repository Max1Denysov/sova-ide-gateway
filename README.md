# GATEWAY

Входная точка запросов бекенда Sova.

## Установка

Директория сервиса с корня:

* `alembic/` описаний миграций для бд
* `components/` компоненты для `rpc` ответов
* `components_utils/` утилиты для компонент
* `env/` файлы окружения для разработки

Файлы:

* `api_world.py` корень всех компонентов
* `tables.py` описания используемых таблиц
* `models.py` модельки для баз данных
* `gateway_server.py` главный скрипт запуска Flask и jsonrpcserver
* `settings.py` файл с настройками, который берёт из окружения нужные переменные и ставит константы
* `processor.py` код из процессора для преобразования шаблонов

## Настройки окружения

Настройки по-умолчанию лежат в `env/develop.env.example`. Для разработки нужно скопировать примеры в файлы без суффикса `.example`.

    cp env/develop.env.example env/develop.env

## Старт базы данных

Используется sqlalchemy. Для миграций нужен sqlalchemy alembic. Описывается структура таблиц и шаги миграции.

Для старта требуются база данных.

Для БД ребуется инициализация uuid расширения:

    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

Миграции лежат в `alembic/`

Статус:

    NLAB_ARM_DEV=1 PYTHONPATH=. PYTHONPATH=. ./venv/bin/alembic current

При пустой базе покажется такое:

    INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
    INFO  [alembic.runtime.migration] Will assume transactional DDL.

Обновиться до последней ревизии:

    NLAB_ARM_DEV=1 venv/bin/alembic upgrade head

## Взаимодействие с процессором

Сервис выполняет проксирование некоторых запросов, например `compiler.*` и `testcase.*` на сервис выполнения задач. Для этого нужно задать настройку хоста сервиса переменной `NLAB_ARM_PROCESSOR_HOST`.

## Запуск приложения

Будут загружены переменные из файла `env/develop.env` и выставлен PYTHONPATH.

    source env/develop.env && \
        export $(cut -d= -f1 env/develop.env) && \
        venv/bin/python gateway_server.py

При использовании файла окружения `env/develop.env` есть шорткат на переменные окружения. Автоматически будут загружены переменные из файла и выставлен PYTHONPATH.

    NLAB_ARM_DEV=1 venv/bin/python gateway_server.py

## Изменение таблиц

Сненерировать миграцию и положить скрипт в alembic:

    NLAB_ARM_DEV=1 PYTHONPATH=. ./venv/bin/alembic revision \
        --autogenerate -m "Added users table"

Скрипт нужно проверить на адекватность и поправить функции `upgrade`/`downgrade` если требуется.

    NLAB_ARM_DEV=1 PYTHONPATH=. ./venv/bin/alembic upgrade VERSION_HASH
    NLAB_ARM_DEV=1 PYTHONPATH=. ./venv/bin/alembic downgrade

И закоммитить.
