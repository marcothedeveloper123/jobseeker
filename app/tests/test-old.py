from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from bs4 import BeautifulSoup
import pandas as pd
import time
from dotenv import load_dotenv
import os
from urllib.parse import urlencode

load_dotenv()

linkedin_email = os.getenv("LINKEDIN_EMAIL")
linkedin_password = os.getenv("LINKEDIN_PASSWORD")

chromedriver_path = "/opt/homebrew/bin/chromedriver"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

driver.implicitly_wait(10)

driver.get("https://www.linkedin.com/login")

email_input = driver.find_element(By.ID, "username")
password_input = driver.find_element(By.ID, "password")
email_input.send_keys(linkedin_email)
password_input.send_keys(linkedin_password)
password_input.send_keys(Keys.ENTER)

time.sleep(10)

for page_num in range(1, 15):
    query = "Data Engineer"
    # location = "European Union"
    # Encode the parameters
    # Remote: f_WT=2
    # European Union: geoId=91000000
    geoId = 91000000
    params = urlencode(
        {
            "keywords": query,
            "geoId": geoId,
            "f_WT": 2,
            "start": (page_num - 1) * 25,
        }
    )
    print(f"Page {page_num}: {params}")
    url = f"https://www.linkedin.com/jobs/search/?{params}"
    driver.get(url)

    # load all cards
    cards = []
    while len(cards) < 25:
        cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        driver.execute_script(
            'arguments[0].scrollIntoView({block: "center", behavior: "smooth"});',
            cards[-1],
        )
        time.sleep(0.5)

    ids = [card.get_attribute("data-job-id") for card in cards]
    titles = [
        title.text
        for title in driver.find_elements(By.CSS_SELECTOR, ".job-card-list__title")
    ]
    companies = [
        company.text
        for company in driver.find_elements(
            By.CSS_SELECTOR, ".job-card-container__company-name"
        )
    ]

    job_time_experience, job_employees_sector, job_description = [], [], []
    for card in cards:
        driver.execute_script(
            'arguments[0].scrollIntoView({block: "center", behavior: "smooth"});', card
        )
        time.sleep(0.5)
        card.click()
        time.sleep(0.5)
        # WebDriverWait(, 10) means that it waits maximum 10 seconds for the element to become visible
        job_time_experience.append(
            WebDriverWait(driver, 10)
            .until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "li.jobs-unified-top-card__job-insight:nth-child(1)")
                )
            )
            .text
        )
        job_employees_sector.append(
            WebDriverWait(driver, 10)
            .until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "li.jobs-unified-top-card__job-insight:nth-child(2)")
                )
            )
            .text
        )
        job_description.append(
            WebDriverWait(driver, 10)
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.jobs-description"))
            )
            .text
        )

    # print results
    pd.DataFrame(
        {
            "Job ID": ids,
            "Job title": titles,
            "Company name": companies,
            "Time & Exp": job_time_experience,
            "Employees & Sector": job_employees_sector,
            "Description": job_description,
        }
    )


# last_height = driver.execute_script("return document.body.scrollHeight")
# while True:
#     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#     new_height = driver.execute_script("return document.body.scrollHeight")
#     if new_height == last_height:
#         break
#     last_height = new_height

# time.sleep(20)  # Wait for 20 seconds

# soup = BeautifulSoup(driver.page_source, "html.parser")

# job_postings = soup.find_all("li", {"class": "jobs-search-results__list-item"})

# Extract relevant information from each job posting and store it in a list of dictionaries
# data = []
# for job_posting in job_postings:
#     try:
#         job_title = (
#             job_posting.find("a", class_="job-card-list__title").get_text().strip()
#         )
#     except AttributeError:
#         job_title = None

#     try:
#         company_name = (
#             job_posting.find("a", class_="job-card-container__link")
#             .get_text()
#             .strip()
#         )
#     except AttributeError:
#         company_name = None

#     try:
#         location = (
#             job_posting.find("li", class_="job-card-container__metadata-item")
#             .get_text()
#             .strip()
#         )
#     except AttributeError:
#         location = None

#     data.append(
#         {"Job Title": job_title, "Company Name": company_name, "Location": location}
#     )

#     df = pd.DataFrame(data)

#     df.to_csv(
#         f"../data/linkedin_jobs_data_engineer_europe_{page_num}.csv", index=False
#     )

driver.quit()
