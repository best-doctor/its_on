#!/bin/bash

if [ -z "$1" ]
  then
    echo "No argument supplied"
    exit 1
elif [ $1 = "migrate" ]
  then
    exec alembic upgrade head
    exit $?
elif [ $1 = "test" ]
  then
    exec make check
    exit $?
elif [ $1 = "run" ]
  then
    rm -rf /srv/www/its_on/static
    cp -r /var/www/its_on/its_on/static /srv/www/its_on
    exec gunicorn --bind 0.0.0.0:8081 --capture-output --access-logfile /var/log/gunicorn/its_on.access.log --workers 3 --worker-class aiohttp.GunicornUVLoopWebWorker its_on.main:init_app
    exit $?
fi
