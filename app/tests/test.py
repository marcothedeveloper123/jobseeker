# Libraries
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# from selenium.common.exceptions import TimeoutException
from urllib.parse import urlencode  # , urlparse, parse_qs
import os
from dotenv import load_dotenv
from pprint import pprint

from bs4 import BeautifulSoup

import pandas as pd


# def get_page_source(url):
#     try:
#         # Open the URL
#         driver.get(url)

#         # Wait for a few seconds to ensure the page loads completely (you can adjust the time)
#         time.sleep(5)

#         # Get the page source
#         page_source = driver.page_source
#     finally:
#         # Close the driver
#         driver.quit()

#     return page_source


# Load environment variables
load_dotenv()

# Initialize the Chrome driver
driver = webdriver.Chrome()

# Maximize Window and set implicit wait
driver.maximize_window()
driver.implicitly_wait(10)

# Enter to the site
driver.get("https://www.linkedin.com/login")
time.sleep(2)

# Accept cookies if the button is present
try:
    cookie_button = driver.find_element(
        By.XPATH, "/html/body/div/main/div[1]/div/section/div/div[2]/button[2]"
    )
    cookie_button.click()
except NoSuchElementException:
    print("No cookie button found")

# User Credentials
user_name = os.getenv("LINKEDIN_EMAIL")
password = os.getenv("LINKEDIN_PASSWORD")

# Login
driver.find_element(By.ID, "username").send_keys(user_name)
driver.find_element(By.ID, "password").send_keys(password)
time.sleep(1)
driver.find_element(By.XPATH, '//*[@id="organic-div"]/form/div[3]/button').click()

# Implicitly wait for elements to load
# driver.implicitly_wait(30)

time.sleep(10)

# Go to search results directly
query = "Data Engineer"
geoId = 91000000  # European Union
f_Wt = 2  # Remote
params = urlencode(
    {
        "keywords": query,
        "geoId": geoId,
        "f_WT": f_Wt,
    }
)

# Number of pages to scrape
num_pages = 5  # You can adjust this as needed
jobs = []

for page_num in range(1, num_pages + 1):
    start = (page_num - 1) * 25
    params = urlencode(
        {"keywords": query, "geoId": geoId, "f_WT": f_Wt, "start": start}
    )
    url = f"https://www.linkedin.com/jobs/search/?{params}"
    driver.get(url)

    # Wait for the job list to load
    job_list_container = WebDriverWait(driver, 1).until(
        EC.presence_of_element_located((By.CLASS_NAME, "scaffold-layout__list"))
    )

    # LinkedIn displays the search results in a scrollable <div> on the left side, we have to scroll to its bottom
    scrollresults = driver.find_element(By.CLASS_NAME, "jobs-search-results-list")

    time.sleep(1)

    # Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
    for i in range(300, 3000, 100):
        driver.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollresults)

    page_source = driver.page_source
    # Parse the HTML source code using BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    # Extract the search result list
    search_result_list = soup.find("div", class_="jobs-search-results-list")
    # pprint(search_result_list)

    # Initialize lists to store the extracted information
    class Job:
        def __init__(
            self,
            job_title,
            company_name,
            location,
            job_link,
            job_id,
            job_description=None,
        ):
            self.job_title = job_title
            self.company_name = company_name
            self.location = location
            self.job_link = job_link
            self.job_id = job_id
            self.job_description = job_description

    index = 0
    # Iterate through each search result item
    for item in search_result_list.find_all(
        "li", class_="jobs-search-results__list-item"
    ):
        print(f"Processing job {index + 1}")

        # Extract the job details with BeautifulSoup
        # Extract job title
        try:
            job_title = item.find("a", class_="job-card-list__title").text.strip()
            # print(job_title)
        except:
            # print("error")
            continue
        # Extract company name
        try:
            company_name = item.find(
                "span", class_="job-card-container__primary-description"
            ).text.strip()
            # print(company_name)
        except:
            # print("error")
            continue
        # Extract location
        try:
            location = item.find(
                "li", class_="job-card-container__metadata-item"
            ).text.strip()
            # print(location)
        except:
            # print("error")
            continue
        # Extract job link
        try:
            job_link = item.find("a", class_="job-card-container__link")["href"]
            # print(job_link)
        except:
            # print("error")
            continue
        # Extract job ID
        try:
            job_id = job_link.split("/view/")[1].split("/")[0]
            # print(job_id)
        except:
            # print("error")
            continue
        # Use Selenium to click the job link
        if job_link:
            try:
                print(f"Clicking on job link: {job_link}")
                clickable_element = driver.find_element(
                    By.XPATH, f"//a[@href='{job_link}']"
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView();", clickable_element
                )
                clickable_element.click()
                time.sleep(2)  # Wait for the job details to load

                # Check for the 'See more' button and click if present
                try:
                    print("Finding 'See more' button")
                    see_more_button = driver.find_element(
                        By.CLASS_NAME, "jobs-description__footer-button"
                    )
                    if see_more_button.is_displayed():
                        print("Clicking 'See more' button")
                        see_more_button.click()
                        time.sleep(1)  # Wait for the full description to load
                except NoSuchElementException:
                    pass  # 'See more' button not found or not needed

                # Extract the job description
                # job_description_element = driver.find_element(By.CLASS_NAME, "jobs-description-content__text")
                # job_description = job_description_element.text.strip() if job_description_element else None

                job_description_element = driver.find_element(
                    By.CLASS_NAME, "jobs-description-content__text"
                )
                job_description = (
                    job_description_element.text.strip()
                    if job_description_element
                    else None
                )

            except NoSuchElementException:
                job_description = None
        try:
            print(f"Adding job number {index + 1} - {job_title}")
            job = Job(
                job_title, company_name, location, job_link, job_id, job_description
            )
            jobs.append(job)
        except:
            # print("error")
            continue
        index += 1

driver.quit()

len(jobs)

# Convert Job objects into dictionaries
job_dicts = [job.__dict__ for job in jobs]

# Create a DataFrame
df = pd.DataFrame(job_dicts)

# Print DataFrame for verification
print(df.head())

# Save the DataFrame as a JSON file
json_file_path = "../data/jobs.json"  # Specify your path here
df.to_json(json_file_path, orient="records", lines=True)

print(f"Data saved to {json_file_path}")