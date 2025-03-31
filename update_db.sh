#!/bin/sh

git pull origin master
cp db/wrkpmp.db db/wrkpmp.db.bak
# python3 compile_job_list_from_companies.py
bash run_test.sh
git add db/*
git commit -m 'cronjob update db'
git push origin master
