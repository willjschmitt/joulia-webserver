#!/bin/bash
python manage.py migrate --noinput
python main.py
