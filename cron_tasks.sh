#! /bin/bash

cd /home/datamade/lametro
/home/datamade/.virtualenvs/lametro/bin/python manage.py import_data >> /tmp/lametro-loaddata.log 2>&1
/home/datamade/.virtualenvs/lametro/bin/python manage.py update_index
