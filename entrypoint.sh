#!/bin/bash
APP_PORT=${PORT:-'8000'}
/opt/venv/bin/gunicorn --worker-tmp-dir /dev/shm expense_app_bot.wsgi:application --bind "0.0.0.0:${APP_PORT}"