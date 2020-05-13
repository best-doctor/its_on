It's on
=======

flag/feature toggle service, written in aiohttp.

API Reference

------
| Method  | Endpoint                            | Description                         |
| ------- | ------------------------------------| ----------------------------------- |
| `GET`   | `/api/docs`                         | Api documentation                   |
| `GET`   | `/api/v1/switch`                    | List of active flags for the group. |

Installing
------

1. Clone repo
    - `$ git clone git@gitlab.com:bestdoctor/public/its_on.git`
2. Install python packages
    - `$ pip install -r requirements.txt`
3. Specify redis connection settings
    - `$ export DYNACONF_REDIS_URL=redis://127.0.0.1:6379/1`
    - default: `redis://127.0.0.1:6379/1`
4. Specify cache settings
    - `$ export DYNACONF_CACHE_URL=redis://127.0.0.1:6379/1`
    - default: `redis://127.0.0.1:6379/1`
5. Specify database connection settings
    - `$ export DYNACONF_DATABASE__dsn=postgresql://user:password@127.0.0.1:5432/its_on`
    - default: `postgresql://bestdoctor:bestdoctor@127.0.0.1:5432/its_on`
6. Apply DB migrations
    - `$ alembic upgrade head`
7. Create user
    - `$ python script/create_user.py --login=admmin --password=passwordd --is_superuser`
8. Run project
    - `$ python -m its_on`
9. Open project
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
