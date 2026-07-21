from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
import uuid
from dotenv import load_dotenv
load_dotenv()


class Analyst():
    def __init__(self):
        #llm = ChatOpenAI(model='gpt-5-mini', temperature=0)  
        llm = ChatOllama(model='gpt-oss:20b', temperature=0)
        memory = InMemorySaver()
        self.agent = create_react_agent(llm, tools=[], checkpointer=memory)

    def is_actually_remote(self, system_prompt, config):
        user_message = {
            "role": "user",
            "content": (
                "The job listing is supposed to be 'Remote'. "
                "Is there any contradictory information about the work location indicating it might not actually be remote? "
                "If you find any contradictory information, reply 'No'. If there is no contradictory information, reply 'Yes'. "
                "Reply only with 'Yes' or 'No', and nothing more."
            )
        }
        messages = [system_prompt, user_message]
        response = self.agent.invoke(
            {"messages": messages},
            config
        )['messages'][-1].content.strip()
        print(f"Remote check response: {response}")
        return response == 'Yes'

    def meets_pay_requirements(self, config, min_annual, min_hourly):
        user_message = {
            "role": "user",
            "content": (
                f"I want to know if the job listing meets my pay requirements of at least ${min_annual} annually or ${min_hourly} hourly. "
                "If a specific rate of pay (or at least a pay range) is NOT included in the listing, reply 'Not mentioned'. "
                "If a range is listed for the pay, only concern yourself with the **maximum** pay rather than the minimum. "
                "Respond with 'Yes' if the pay meets the aforementioned requirements or 'No' if it fails to meet the requirements. "
                "Your response should only be one of the following and nothing more: 'Yes', 'No', 'Not mentioned'"
            )
        }
        response = self.agent.invoke(
            {"messages": [user_message]},
            config
        )['messages'][-1].content.strip()
        print(f"Pay check response: {response}")
        return response != 'No'
    
    def qualification_score(self, config, resume_text):
        user_message = {
            "role": "user",
            "content": (
                "Based on the contents of the resume below, rate how qualified the applicant is for the job listing on a scale of 1 to 100, with 100 being the perfect candidate for the job. "
                "**Do not factor college education requirements into your decision.** "
                f"Resume: \n{resume_text} "
                "Your response should only be a single integer from 1 to 100 and nothing more."                
            )
        }
        response = self.agent.invoke(
            {"messages": [user_message]},
            config
        )['messages'][-1].content.strip()
        print(f"Qualification score response: {response}")
        return response
    
    def analyze_job_listing(self, job, minimum_annual, minimum_hourly, resume_text):
        result = {
            'is_actually_remote': None,
            'meets_pay_requirements': None,
            'qualification_score': None
        }
        system_prompt = {
            "role": "system",
            "content": (
                "Your job to analyze the contents of the following job listing and determine if it meets the user's specified criteria: \n\n"
                f"{job}"
            )
        }
        guid = str(uuid.uuid4())
        config = {"configurable": {"thread_id": guid}}

        # check if it's actually remote
        is_remote = self.is_actually_remote(system_prompt, config)
        result['is_actually_remote'] = is_remote
        if not is_remote:
            return result

        # check if it meets pay requirements
        meets_pay = self.meets_pay_requirements(config, minimum_annual, minimum_hourly)
        result['meets_pay_requirements'] = meets_pay
        if not meets_pay:
            return result
        
        # get qualification score
        qualification_score = self.qualification_score(config, resume_text)
        result['qualification_score'] = qualification_score
        return result

