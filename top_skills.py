import json
import os
import re

import pandas as pd
from dotenv import load_dotenv
from joblib import dump, load
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tqdm import tqdm
tqdm.pandas()

load_dotenv()


if not os.listdir('cache'):
    with open("remaining_jobs.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    dump(df, "cache/processed_jobs.joblib")
else:
    df = load("cache/processed_jobs.joblib")

llm = ChatOllama(model='gpt-oss:20b', temperature=0)
# llm = ChatOpenAI(model='gpt-5-mini', temperature=0)
agent = create_react_agent(llm, tools=[])

def get_skills(description):
    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": (
                    "List the specific technical skills (programming languages, frameworks, software etc.) mentioned in the following job description, separated by commas. "
                    f"Job description: \n\n{description}"
                )
            }
        ]
    })
    skills = response['messages'][-1].content.strip()
    return skills

if not os.path.exists('cache/jobs_skills.joblib'):
    df['skills'] = None
    df['skills'] = df['description'].progress_apply(get_skills)
    dump(df, 'cache/jobs_skills.joblib')
else:
    df = load('cache/jobs_skills.joblib')

unique_skills = set()
all_skills = []

for idx, row in df.iterrows():
    skills = row['skills']
    print(skills)
    skills = skills.split(', ')
    for s in skills:
        unique_skills.add(s)
        all_skills.append(s)

skill_counts = {}
for s in all_skills:
    if s not in skill_counts:
        skill_counts[s] = 0
    else:
        skill_counts[s] += 1

skill_counts_sorted = sorted(skill_counts.items(), key=lambda item: item[1], reverse=True)
print(skill_counts_sorted)

with open('skill_counts.json', "w", encoding="utf-8") as f:
    json.dump(skill_counts_sorted, f, indent=2, ensure_ascii=False)
