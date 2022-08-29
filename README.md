# It's on

[![Build Status](https://github.com/best-doctor/its_on/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/best-doctor/its_on/actions/workflows/build.yml)
[![Test Coverage](https://api.codeclimate.com/v1/badges/35e678c4d05199a31eb9/test_coverage)](https://codeclimate.com/github/best-doctor/its_on/test_coverage)

Flag/feature toggle service, written in aiohttp.

## API Reference

### Basic

| Method  | Endpoint                         | Description                             |
| ------- |----------------------------------|-----------------------------------------|
| `GET`   | `/api/docs`                      | Api documentation                       |
| `GET`   | `/api/v1/switch`                 | List of flags for the group.            |
| `GET`   | `/api/v1/switches/{id}/svg-badge` | SVG badge with actual flag information |
| `GET`   | `/api/v1/switches_full_info` | List of all active flags with full info. |

### Admin

| Endpoint                        | Description                |
| --------------------------------| -------------------------- |
| `/zbs/login`                    |  Login form                |
| `/zbs/switches`                 |  List of flags             |
| `/zbs/switches/{switch_id}`     |  Flag detail               |

## Sample /api/v1/switch output

```json
{
    "count": 2,
    "result": ["test_flag3", "test_flag4"]
}
```

## SVG badges

SVG badges can be useful for showing actual feature flag states.

Open `Flag detail` page, find `SVG badge` section and copy badge.

<details>
  <summary>Screenshot</summary>

  ![admin-flag-editing-page](docs/assets/img/admin-flag-editing-page.png)

</details>

You will get an image with a link in Markdown format:

```markdown
[![flag-name](link-to-svg-badge)](link-to-flag-editing-page)
```

Then paste text in a text editor with Markdown support (task tracker, Slack, Mattermost etc.).
Actual flag state will be displayed as follows:

| State         | Badge                                                             |
|---------------|-------------------------------------------------------------------|
| Active flag   | ![active-flag-badge](its_on/static/img/active-flag-badge.svg)     |
| Inactive flag | ![inactive-flag-badge](its_on/static/img/inactive-flag-badge.svg) |
| Deleted flag  | ![deleted-flag-badge](its_on/static/img/deleted-flag-badge.svg)   |
| Unknown flag  | ![unknown-flag-badge](its_on/static/img/unknown-flag-badge.svg)   |

See [settings.yaml](settings.yaml) for additional settings.

## Installation

### Prerequisites

`its_on` requires an SQL database and a cache storage engine.
Currently, only PostgreSQL and Redis are supported as respective backends.

### Manual

Clone repo:

`$ git clone git@gitlab.com:bestdoctor/public/its_on.git`

Install python packages:

`$ pip install -r requirements.txt`

Specify database and cache settings:

```env
export DYNACONF_REDIS_URL=redis://127.0.0.1:6379/1
export DYNACONF_CACHE_URL=redis://127.0.0.1:6379/1
export DYNACONF_DATABASE__dsn=postgresql://user:password@127.0.0.1:5432/its_on
```

Apply database migrations:

`$ alembic upgrade head`

Create admin user:

`$ python scripts/create_user.py --login=admin --password=password --is_superuser`

Run server:

`$ python -m its_on`

Navigate to `http://127.0.0.1:8081/api/docs` in your browser
and you are good to go!

### Docker

Example `docker-compose.yml` file:

```yaml
version: '3'
services:
  cache:
    image: redis
    container_name: its-on-redis

  db:
    image: postgres
    container_name: its-on-postgres
    environment:
      POSTGRES_PASSWORD: strongpassword
      POSTGRES_USER: itson
      POSTGRES_DB: itson

  web:
    image: bestdoctor/its_on:latest-dev
    container_name: its-on
    environment:
      DYNACONF_HOST: '0.0.0.0'
      DYNACONF_DATABASE__dsn: postgresql://itson:strongpassword@db:5432/itson
      DYNACONF_REDIS_URL: redis://cache:6379/0
      DYNACONF_CACHE_URL: redis://cache:6379/1
    ports:
     - "127.0.0.1:8081:8081"
    depends_on:
      - cache
      - db

```

Don't forget to create a superuser:

```bash
docker exec -t its-on python scripts/create_user.py --login=admin \
                                                    --password=password \
                                                    --is_superuser
```

Navigate to `http://127.0.0.1:8081/api/docs` in your browser and
you are good to go!

## Testing

Run `make test`

## Contributing

We would love you to contribute to our project. It's simple:

- Create an issue with bug you found or proposal you have.
  Wait for approve from maintainer.
- Create a pull request. Make sure all checks are green.
- Fix review comments if any.
- Be awesome.

Here are useful tips:

- You can run all checks and tests with `make check`. Please do it
  before CI does.
- We use
  [BestDoctor python styleguide](https://github.com/best-doctor/guides/blob/master/guides/python_styleguide.md).
  Sorry, styleguide is available only in Russian for now.
- We respect [Django CoC](https://www.djangoproject.com/conduct/).
  Make soft, not bullshit.
