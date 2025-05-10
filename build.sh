#!/usr/bin/env bash
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python manage.py collectstatic --noinput
python manage.py migrate
