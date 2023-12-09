from langchain.llms import Ollama
import pandas as pd
from tqdm import tqdm
import json
from pydantic import BaseModel, ValidationError
from typing import List
import logging

GREEN = "\033[92m"
RESET = "\033[0m"

# Basic configuration for logging
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Define the Pydantic model for skill data
class Skill(BaseModel):
    skill: str
    reference: str


# Initialize the LLM model
model = Ollama(
    model="neural-chat:7b-v3.2-fp16",
    temperature=0.7,
    # Additional model configuration can go here
)

# File names for the output JSON files
file_name = "../data/skills.json"
unparsed_file_name = "../data/unparsable.json"

# Lists to hold parsed and unparsed skills
skills = []
unparsed = []

# Define the desired JSON format for the skills
desired_format = """
[{ "skill": <string: keywords—max 3 words>, "reference": <string: sentence from description>},
{ "skill": <string: keywords—max 3 words>, "reference": <string: sentence from description>}]
"""

# Read the CSV file containing job postings
job_postings = pd.read_csv("../data/jobs_data_engineer_-_103644278_-_2_-_LinkedIn.csv")
descriptions = job_postings["job_description"].to_list()


# Loop through each description
with tqdm(
    total=len(descriptions), desc="Extracting skills", unit="skill"
) as skills_pbar:
    for description in descriptions:
        # Generate the LLM prompt
        prompt = f"""
        Extract the required skills (max 3 words per skill) from the following job description, as well as the reference sentence in the job description from which you extracted the skill. Respond in JSON format.
        \n
        {description}
        Your response in json format — {desired_format}:
        """

        # Get the response from the LLM
        skill_json_string = model(prompt)
        logging.info(f"LLM Response: {skill_json_string}")

        # Parse the JSON string to a Python object
        try:
            new_skills = json.loads(skill_json_string)
            logging.info(f"Parsed Skills: {new_skills}")

            # Process each skill item in the response
            for skill_data in new_skills:
                if isinstance(skill_data, dict) and "skill" in skill_data:
                    if isinstance(skill_data["skill"], list):
                        # Process each skill in the list
                        for individual_skill in skill_data["skill"]:
                            try:
                                skill = Skill(
                                    skill=individual_skill,
                                    reference=skill_data["reference"],
                                )
                                # pprint(skill)
                                skills.append(skill.model_dump())
                            except ValidationError as e:
                                logging.error(f"Data validation error: {e}")
                    elif isinstance(skill_data["skill"], str):
                        # Process a single skill string
                        try:
                            skill = Skill(**skill_data)
                            skills.append(skill.model_dump())
                        except ValidationError as e:
                            logging.error(f"Data validation error: {e}")
                    else:
                        # Flag as unparsable if not a list or string
                        unparsed.append(skill_data)
                else:
                    # Flag as unparsable if not a dictionary with a 'skill' key
                    unparsed.append(skill_data)
        except json.JSONDecodeError:
            # If JSON parsing fails, add the entire response to unparsable
            unparsed.append(skill_json_string)

        # Write the skills to a JSON file after each update
        with open(file_name, "w") as file:
            json.dump(skills, file, indent=4)

        # Write unparsable items to a JSON file after each update
        if unparsed:
            with open(unparsed_file_name, "w") as file:
                json.dump(unparsed, file, indent=4)

        # Update the progress bar and display the count of unparsable items
        skills_pbar.set_description(f"Extracting skills (Unparsable: {len(unparsed)})")
        skills_pbar.update(1)

# Print completion messages
print(f"{GREEN}Saved skills to {file_name}{RESET}")
print(f"{GREEN}Unparsable items saved to {unparsed_file_name}{RESET}")