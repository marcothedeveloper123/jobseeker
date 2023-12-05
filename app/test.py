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


def get_page_source(url):
    try:
        # Open the URL
        driver.get(url)

        # Wait for a few seconds to ensure the page loads completely (you can adjust the time)
        time.sleep(5)

        # Get the page source
        page_source = driver.page_source
    finally:
        # Close the driver
        driver.quit()

    return page_source


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

    page_source = driver.page_source
    # Parse the HTML source code using BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    # Extract the search result list
    search_result_list = soup.find("div", class_="jobs-search-results-list")
    # pprint(search_result_list)

    # Initialize lists to store the extracted information
    class Job:
        def __init__(self, job_title, company_name, location, job_link, job_id):
            self.job_title = job_title
            self.company_name = company_name
            self.location = location
            self.job_link = job_link
            self.job_id = job_id

    # Iterate through each search result item
    for item in search_result_list.find_all(
        "li", class_="jobs-search-results__list-item"
    ):
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
        try:
            job = Job(job_title, company_name, location, job_link, job_id)
            jobs.append(job)
        except:
            # print("error")
            continue

driver.quit()

pprint(jobs)
len(jobs)