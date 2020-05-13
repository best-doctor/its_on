It's on
=======

flag/feature toggle service, written in aiohttp.

API Reference

------
| Method  | Endpoint                   | Description                         |
| ------- | ---------------------------| ----------------------------------- |
| `GET`   | `/api/docs`                | Api documentation                   |
| `GET`   | `/api/v1/switch`           | List of active flags for the group. |

Installing
------

1. Clone repo
    - `$ git clone git@gitlab.com:bestdoctor/public/its_on.git`
1. Install python packages
    - `$ pip install -r requirements.txt`
1. Specify redis connection settings
    - `$ export DYNACONF_REDIS_URL=redis://127.0.0.1:6379/1`
    - default: `redis://127.0.0.1:6379/1`
1. Specify cache settings
    - `$ export DYNACONF_CACHE_URL=redis://127.0.0.1:6379/1`
    - default: `redis://127.0.0.1:6379/1`
1. Specify database connection settings
    - `$ export DYNACONF_DATABASE__dsn=postgresql://user:password@127.0.0.1:5432/its_on`
    - default: `postgresql://bestdoctor:bestdoctor@127.0.0.1:5432/its_on`
1. Apply DB migrations
    - `$ alembic upgrade head`
1. Create user
    - `$ python script/create_user.py --login=admmin --password=passwordd --is_superuser`
1. Run project
    - `$ python -m its_on`
1. Open project
    - `open http://localhost:8081/api/docs`

Testing
------

`$ make test`

Admin
------

| Endpoint                        | Description                |
| --------------------------------| -------------------------- |
| `/zbs/login`                    |  Login form                |
| `/zbs/switches`                 |  List of flags             |
| `/zbs/switches/{switch_id}`     |  Flag detail               |
