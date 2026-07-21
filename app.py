from scraper import scrape_indeed
from analyst import Analyst
import docx2txt
import json

MIN_ANNUAL = 105000
MIN_HOURLY = 52
RESUME_FILENAME = "Cody Mayers Resume.docx"

search_params = {
    "q": "python", # keyword
    "l": "Remote" # location
}

jobs = scrape_indeed(search_params, max_pages=10)
print(f"Found {len(jobs)} jobs")

not_enough_pay = []
not_remote = []
remaining_jobs = []

# read resume text
resume_text = docx2txt.process(RESUME_FILENAME)

jobs_checked = 0
analyst = Analyst()
for job in jobs:
    result = analyst.analyze_job_listing(
        job['description'], 
        MIN_ANNUAL, 
        MIN_HOURLY,
        resume_text
    )
    if not result['is_actually_remote']:
        not_remote.append(job)
    elif not result['meets_pay_requirements']:
        not_enough_pay.append(job)
    else:
        job['qualification_score'] = result['qualification_score']
        remaining_jobs.append(job)
    jobs_checked += 1
    print(f'Checked {jobs_checked} jobs.')

print('Filtered all jobs.')
print(f'Found {len(not_enough_pay)} jobs not meeting your pay requirements.')
print(f'Found {len(not_remote)} jobs that were not actually remote.')

excluded_jobs = {
    'not_enough_pay': not_enough_pay,
    'not_remote': not_remote
}

# write excluded jobs to a json file
with open('excluded_jobs.json', 'w', encoding='utf-8') as f:
    json.dump(excluded_jobs, f, ensure_ascii=False, indent=4)

# sort remaining jobs by qualification score
remaining_jobs.sort(key=lambda x: int(x['qualification_score']), reverse=True)

# write remaining jobs to a json file
with open('remaining_jobs.json', 'w', encoding='utf-8') as f:
    json.dump(remaining_jobs, f, ensure_ascii=False, indent=4)