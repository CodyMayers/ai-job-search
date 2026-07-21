import json
import os
import hashlib
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def get_cache_filename(params):
    """Generate cache filename based on search params."""
    hash_key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
    return f"indeed_cache_{hash_key}.json"

def scrape_indeed(params, max_pages=1):
    cache_file = get_cache_filename(params)
    if os.path.exists(cache_file):
        print(f"Loading results from cache: {cache_file}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Attach to existing Chrome instead of launching a new one
    options = Options()
    options.debugger_address = "127.0.0.1:9222"   # match the port from Step 1

    driver = webdriver.Chrome(options=options)

    base_url = "https://www.indeed.com/jobs"
    query_string = "&".join([f"{k}={v.replace(' ', '+')}" for k, v in params.items()])
    results = []

    try:
        for page in range(max_pages):
            print('Page', page + 1)
            start = page * 10
            url = f"{base_url}?{query_string}&start={start}"
            driver.get(url)
            time.sleep(3)  # allow page load

            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")

            card_num = 0
            for card in job_cards:
                card_num += 1
                print('Card', card_num)
                job = {}
                try:
                    job_title = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span")
                    job["title"] = job_title.text
                    job["company"] = card.find_element(By.CLASS_NAME, "company_location").find_element(By.XPATH, "./*[1]").find_element(By.XPATH, "./*[1]").text
                    link_elem = card.find_element(By.CSS_SELECTOR, "a")
                    job["link"] = link_elem.get_attribute("href")
                    # click the card to open the job listing to the right
                    job_title.find_element(By.XPATH, "..").click()
                    time.sleep(3)
                    job["description"] = driver.find_element(By.ID, "jobDescriptionText").text
                except:
                    continue

                results.append(job)

            time.sleep(2)  # throttle requests

    finally:
        # Don’t quit the driver, since it’s your real Chrome window
        pass

    # Save to cache
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results

if __name__ == '__main__':
    search_params = {
        "q": "python", # keyword
        "l": "Remote" # location
    }

    jobs = scrape_indeed(search_params, max_pages=10)
    print(f"Found {len(jobs)} jobs")