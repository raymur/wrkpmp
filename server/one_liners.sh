# get a list of companies sorted from the most jobs to the least
cat good_list/company_jobs.csv | cut -d ',' -f 1  | sort  | uniq -c | sort  -r | less
