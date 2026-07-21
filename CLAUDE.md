# ai-job-search

Personal Indeed job-search automation pipeline: scrape listings → filter/score them with a local LLM → summarize the most in-demand skills across the best-fit listings.

## Pipeline

Runs in this order:

1. **`scraper.py`** — Selenium-driven Indeed scraper. Attaches to an already-running Chrome instance over CDP (`--remote-debugging-port=9222`) rather than launching its own browser, so it reuses the user's logged-in Indeed session (see Setup below). Searches by keyword/location (`q`, `l` params), paginates, and scrapes title/company/link/description per listing. Results are cached to `indeed_cache_<md5-of-params>.json` at repo root, keyed by the search params — delete the file to force a re-scrape.

2. **`analyst.py`** — `Analyst` class wrapping a LangGraph `create_react_agent` over an LLM (defaults to local Ollama `gpt-oss:20b`; `ChatOpenAI`/`gpt-5-mini` is available but commented out in the source). For each job it runs three gated checks, short-circuiting on the first failure:
   - Is it actually remote (checks for contradictions in the listing text)?
   - Does the pay meet the configured minimums?
   - If both pass, score fit 1–100 against the resume text.

3. **`app.py`** — Orchestrator / entry point. Scrapes, loads the resume via `docx2txt`, runs every job through `Analyst`, then writes:
   - `excluded_jobs.json` — jobs split into `not_enough_pay` / `not_remote`
   - `remaining_jobs.json` — qualifying jobs, sorted by qualification score (descending)

   Search criteria are hardcoded at the top of this file: `MIN_ANNUAL`, `MIN_HOURLY`, `RESUME_FILENAME`, and the `search_params` dict (`q`, `l`). Edit there to change what's searched for or filtered on.

4. **`top_skills.py`** — Second pass over `remaining_jobs.json`. Asks the LLM to extract technical skills per listing, tallies frequency across all listings, and writes `skill_counts.json`. Caches intermediate pandas DataFrames as `.joblib` files in `cache/` (`processed_jobs.joblib`, `jobs_skills.joblib`) so re-runs don't repeat LLM calls.

## Setup / running

1. Launch Chrome in remote-debugging mode, pointed at your normal profile, and sign into Indeed in that window:
   ```
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\<you>\AppData\Local\Google\Chrome\User Data\Default"
   ```
   Leave that window open — `scraper.py` attaches to it rather than opening a new browser.

2. No dependency manifest is tracked in this repo (no `requirements.txt`/`pyproject.toml`) — only a local `venv/`. Key packages currently installed: `selenium`, `beautifulsoup4`, `langgraph`, `langchain-ollama`, `langchain-openai`, `openai`, `pandas`, `joblib`, `docx2txt`, `python-dotenv`. Run `pip freeze` inside `venv/` if you need the full/exact list.

3. LLM backend: defaults to a local Ollama model (`gpt-oss:20b` — requires Ollama running with that model pulled). To use OpenAI instead, uncomment the `ChatOpenAI` lines in `analyst.py`/`top_skills.py` and set `OPENAI_API_KEY` in `.env` (already present, gitignored).

4. Run `python app.py` to scrape + filter, then `python top_skills.py` to analyze skill frequency across the results.

## Notes

- No automated tests exist in this repo.
- Indeed's DOM selectors in `scraper.py` (`div.job_seen_beacon`, `h2.jobTitle span`, `company_location`, `#jobDescriptionText`) are fragile and likely to break silently if Indeed changes its markup — if scraping returns empty/malformed results, check these first.
- Generated artifacts (`indeed_cache_*.json`, `remaining_jobs.json`, `excluded_jobs.json`, `skill_counts.json`, `cache/*.joblib`) are reproducible outputs, not source — safe to delete and regenerate. They're gitignored.
