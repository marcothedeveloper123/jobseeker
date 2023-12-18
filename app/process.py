from langchain.llms import Ollama

from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import pandas as pd
from pydantic import BaseModel, ValidationError
import json
import logging

# set up logging at level info
logging.basicConfig(level=logging.INFO)


class Response(BaseModel):
    skills: list
    reference: str


def parse_and_yield(json_str):
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            # Data is not a list, need to re-prompt
            return None

        for item in data:
            if not isinstance(item, dict) or "reference" not in item:
                # Item structure is not as expected, need to re-prompt
                return None

            # Check and format 'skills'
            if "skills" in item:
                if isinstance(item["skills"], str):
                    item["skills"] = [item["skills"]]
                elif not isinstance(item["skills"], list):
                    # 'skills' is neither a string nor a list, need to re-prompt
                    return None
            else:
                # 'skills' key not found, use an empty list
                item["skills"] = []

            yield item

    except json.JSONDecodeError:
        # JSON is unparsable, need to re-prompt
        return None


def ask_llm(model, prompt):
    print(f"Prompting LLM...")
    response = model(prompt)
    return response


model = Ollama(
    model="mistral-openorca:7b-fp16",
    temperature=0.7,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
    verbose=True,
)

job_postings = pd.read_json(
    "../data/bronze/marco_script/ai_application_developer_United_States.json"
)
descriptions = job_postings["description"].to_list()

desired_format = """
[{ "skills": <keywords>, "reference": <sentence from description>}]
"""

example = """
Designing the application in line with established usability principles and business requirements;
[{ "skills": ["business requirements analysis", "semantic models", "conversation flow", "machine learning", "rule-based techniques", "java", "javascript", "python"], "reference": "Working with customers to analyze and understand business requirements;
Designing the application in line with established usability principles and business requirements;
Implementing and testing the semantic models and the conversation flow, using both machine learning and rule-based techniques;
Using Java/JavaScript/Python to code application logic;
Analyzing real-life human-system dialogs, assessing the overall system performance, and identifying improvement opportunities"}]
"""

for test_output in descriptions:
    valid_response = False
    while not valid_response:
        prompt = f"""
        You are a helpful job posting summarization assistant. You help job seekers identify the skills they need to be successful in their job.
        To do that, you summarize job descriptions by extracting just the salient job skills and references from job descriptions. You are not exhaustive;
        you only highlight the salient job skills and references.
        Your responses should be in the following format:\n\n
        {desired_format}\n\n
        Your response will be used in a json parser, so please respond only with the json object. Here is an example output:\n\n
        {example}\n\n
        Now take a deep breath and extract the salient job skills, with the reference text to those skills, from the following description: {test_output}
        """
        llm_response = ask_llm(model, prompt)
        for item in parse_and_yield(llm_response):
            if item is not None:
                response_obj = Response(**item)
                print("\nResponse:")
                print(response_obj)
                valid_response = True
            else:
                print("Invalid response. Reprompting the LLM.")
