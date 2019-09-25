It's on
=======

Микросервис для работы с фича флагами на aiohttp.

HOW TO
------

`python -m its_on` – запуск сервера.
`/api/docs` - Документация api


Установка dev
------

1. Клонировать репозиторий
2. pip install -r requirements.txt
3. Создать БД или переопределить настройки подключения к БД.
    1. По умолчанию:
        - название БД - its_on
        - пользователь - bestdoctor
        - пароль - bestdoctor
    2. Переопределение настроек БД - `export DYNACONF_DATABASE__dsn=postgresql://bestdoctor:bestdoctor@127.0.0.1:5432/its_on_test`
4. Накатить миграции `alembic upgrade head`
