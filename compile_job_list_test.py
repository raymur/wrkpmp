from compile_job_list_from_companies import *
import logging


def test_single_company():
  logger.setLevel(level=logging.DEBUG)
  new_job_count = 0
  companies = ['appviewxrebound']
  for company in companies:
    current_job_ids = lookup_jobs(company)
    logger.debug(current_job_ids)
    new_job_count += len(current_job_ids)
  print(f"added {new_job_count} new jobs")
  assert True