#!/bin/bash

while true; do

    flask db upgrade
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Upgrade command failed, retrying in 5 secs...
    sleep 5
done

export PYTHONPATH=$PYTHONPATH:./kinetics_db

exec gunicorn -b :5000 --access-logfile - --error-logfile - kinetics_db:app
