import logging


class CustomFormatter(logging.Formatter):
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.ERROR: RED + FORMAT + RESET,
        logging.DEBUG: BLUE + FORMAT + RESET,
        logging.INFO: FORMAT,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.CRITICAL: RED + FORMAT + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


# Configure logging with the custom formatter
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Set the custom formatter
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.error import URLError
from bs4 import BeautifulSoup
import re
from pydantic import BaseModel
import time
from tqdm import tqdm

load_dotenv()

CHROME_BINARY_LOCATION = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

LOGIN_URL_LINKEDIN = "https://www.linkedin.com/login"
LOGIN_BUTTON_XPATH_LINKEDIN = '//*[@id="organic-div"]/form/div[3]/button'
EXPECTED_URL_LINKEDIN = "https://www.linkedin.com/feed/"
COOKIE_BUTTON_XPATH_LINKEDIN = (
    "/html/body/div/main/div[1]/div/section/div/div[2]/button[2]"
)
SEARCH_RESULTS_LIST_CLASS_LINKEDIN = "jobs-search-results-list"
JOB_LIST_ITEM_CLASS_LINKEDIN = "jobs-search-results__list-item"
LINK_CLASS_LINKEDIN = "job-card-container__link"
DESCRIPTION_CLASS_LINKEDIN = "jobs-description-content__text"
TITLE_CLASS_LINKEDIN = "job-card-list__title"
LOCATION_CLASS_LINKEDIN = "job-card-container__metadata-item"
COMPANY_NAME_CLASS_LINKEDIN = "job-card-container__primary-description"
END_OF_RESULTS_LIST_LINKEDIN = "global-footer-compact"
SEARCH_RESULTS_PER_PAGE_LINKEDIN = 25
USERNAME_ID_LINKEDIN = "username"
PASSWORD_ID_LINKEDIN = "password"
PROFILE_PIC_CLASS_LINKEDIN = "global-nav__me-photo"
TOTAL_SEARCH_RESULTS_STRING_LINKEDIN = "jobs-search-results-list__subtitle"


def set_up_selenium():
    options = webdriver.ChromeOptions()
    options.binary_location = CHROME_BINARY_LOCATION
    # options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=options)
    logging.info("Webdriver initialized")
    driver.implicitly_wait(10)

    return driver


class LinkedIn:
    login_url = LOGIN_URL_LINKEDIN
    username = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    login_button_xpath = LOGIN_BUTTON_XPATH_LINKEDIN
    expected_url = EXPECTED_URL_LINKEDIN
    cookie_button_xpath = COOKIE_BUTTON_XPATH_LINKEDIN
    search_results_list_class = SEARCH_RESULTS_LIST_CLASS_LINKEDIN
    job_list_item_class = JOB_LIST_ITEM_CLASS_LINKEDIN
    link_class = LINK_CLASS_LINKEDIN
    description_class = DESCRIPTION_CLASS_LINKEDIN
    title_class = TITLE_CLASS_LINKEDIN
    location_class = LOCATION_CLASS_LINKEDIN
    company_name_class = COMPANY_NAME_CLASS_LINKEDIN
    end_of_results_list_class = END_OF_RESULTS_LIST_LINKEDIN
    search_results_per_page = SEARCH_RESULTS_PER_PAGE_LINKEDIN
    username_id = USERNAME_ID_LINKEDIN
    password_id = PASSWORD_ID_LINKEDIN
    profile_pic_class = PROFILE_PIC_CLASS_LINKEDIN
    total_search_results_string = TOTAL_SEARCH_RESULTS_STRING_LINKEDIN

    def __init__(self, query):
        if not self.is_valid_url(query):
            raise ValueError(f"Invalid URL: {query}")
        self.query = query
        logging.info(f"Initialized LinkedIn with query: {self.query}")

    def compose_url(self, page):
        parsed_url = urlparse(self.query)
        original_query_params = parse_qs(parsed_url.query)

        required_params = {"f_WT", "geoId", "location", "keywords"}
        if not required_params.issubset(set(original_query_params.keys())):
            raise ValueError(
                f"Missing required parameters: {required_params - set(original_query_params.keys())}"
            )

        query_params = {
            k: v for k, v in original_query_params.items() if k not in ["start"]
        }
        query_params["start"] = [str(page * 25)]

        final_url = parsed_url._replace(
            query=urlencode(query_params, doseq=True)
        ).geturl()

        if not self.is_valid_url(final_url):
            raise ValueError(f"Final URL invalid: {final_url}")

        return final_url

    def update_query(self, page):
        self.query = self.compose_url(page)
        logging.info(f"Updated query: {self.query}")

    @staticmethod
    def is_valid_url(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except (ValueError, URLError):
            logging.error(f"Invalid URL: {url}")
            return False


def log_in(driver, site):
    # navigate to LinkedIn
    login_url = site.login_url
    driver.get(login_url)

    # accept cookies
    cookie_button_xpath = site.cookie_button_xpath
    # cookie_button = driver.find_element(By.XPATH, cookie_button_xpath)
    try:
        WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))
        ).click()
    except NoSuchElementException:
        logging.info("No cookies button found.")
        pass

    # log into LinkedIn
    try:
        WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.ID, site.username_id))
        ).send_keys(site.username)
        WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.ID, site.password_id))
        ).send_keys(site.password)
        WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.XPATH, site.login_button_xpath))
        ).click()
    except WebDriverException:
        logging.error("Login failed. Please check your credentials.")
        exit(1)

    # wait = input("Press enter to continue")
    WebDriverWait(driver, 300).until(EC.url_to_be(site.expected_url))

    # Check for the presence of the user avatar to confirm successful login
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, site.profile_pic_class))
        )
        logging.info("Successfully logged in.")
    except TimeoutException as e:
        logging.error("Login failed. User avatar not found: {e}")
        exit(1)


def prepare_search_results_page(driver, site, current_page):
    # navigate to search results
    try:
        logging.info(
            f"Preparing search results for page {site.compose_url(current_page - 1)}"
        )
        driver.get(site.compose_url(current_page - 1))
        # Wait for the pagination element to be present
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, site.end_of_results_list_class)
            )
        )
        total_results = driver.find_element(
            By.CLASS_NAME, site.total_search_results_string
        ).text

        match = re.search(r"[\d,]+", total_results)
        if match:
            total_results = int(match.group().replace(",", ""))
        else:
            total_results = 25

        logging.info("Successfully loaded end of results list")
    except WebDriverException as e:
        logging.error(
            "Failed to prepare search result page. Please check your query: {e}"
        )
        exit(1)

    return total_results


def load_search_results(driver, site, total_results, current_page):
    expected_results = calculate_expected_results(
        total_results=total_results,
        current_page=current_page,
        search_results_per_page=site.search_results_per_page,
    )
    retry_count = 0
    max_retries = 5  # Set a limit for retries before asking for user input

    while True:
        try:
            driver_job_list = driver.find_elements(
                By.CLASS_NAME, site.job_list_item_class
            )
            page_source = BeautifulSoup(driver.page_source, "html.parser")
            job_list = page_source.find_all("li", class_=site.job_list_item_class)

            if (
                len(driver_job_list) >= expected_results
                and len(job_list) >= expected_results
            ):
                if is_selenium_element_loaded(
                    driver_job_list[-1]
                ) and is_bs_element_loaded(job_list[-1], site):
                    logging.info("Found all job results")
                    return driver_job_list, job_list

            scroll_list(driver, site)
            time.sleep(1.5)

        except WebDriverException as e:
            retry_count += 1
            logging.error(
                f"Failed to load search results. Please check your query: {e}"
            )

            # Check if the retry limit is reached
            if retry_count >= max_retries:
                user_input = input(
                    "Failed to load all results. Press Enter to try again or Ctrl+C to interrupt the process."
                )
                retry_count = 0  # Reset retry count after user input
            else:
                logging.info(f"Retrying... Attempt {retry_count + 1}/{max_retries}")

    # If the loop exits without returning, it means the process was interrupted
    logging.info("Process interrupted by the user.")


def load_search_results_old(driver, site, total_results, current_page):
    expected_results = calculate_expected_results(
        total_results=total_results,
        current_page=current_page,
        search_results_per_page=site.search_results_per_page,
    )
    try:
        while True:
            driver_job_list = driver.find_elements(
                By.CLASS_NAME, site.job_list_item_class
            )
            page_source = BeautifulSoup(driver.page_source, "html.parser")
            job_list = page_source.find_all("li", class_=site.job_list_item_class)
            djl = len(driver_job_list)
            jl = len(job_list)
            if djl >= expected_results and jl >= expected_results:
                if is_selenium_element_loaded(
                    driver_job_list[-1]
                ) and is_bs_element_loaded(job_list[-1], site):
                    logging.info("found all job results")
                    break
            scroll_list(driver, site)
            time.sleep(1.5)
        return driver_job_list, job_list
    except WebDriverException as e:
        logging.error(f"Failed to load search results. Please check your query: {e}")
        exit(1)


def is_selenium_element_loaded(driver_element):
    try:
        # Check if the necessary elements are present and not empty
        if not driver_element.find_element(By.CLASS_NAME, site.link_class).text.strip():
            return False
        if not driver_element.find_element(
            By.CLASS_NAME, site.company_name_class
        ).text.strip():
            return False
        if not driver_element.find_element(
            By.CLASS_NAME, site.location_class
        ).text.strip():
            return False
        if (
            not driver_element.find_element(By.CLASS_NAME, site.link_class)
            .get_attribute("href")
            .strip()
        ):
            return False
        # Add more checks as necessary for other elements
    except NoSuchElementException:
        # If any element is not found, the content is not fully loaded
        return False
    return True


def is_bs_element_loaded(bs_element, site):
    try:
        # Check if the necessary elements are fully loaded
        if not bs_element.find("a", class_=site.link_class).get_text(strip=True):
            return False
        if not bs_element.find("span", class_=site.company_name_class).get_text(
            strip=True
        ):
            return False
        if not bs_element.find("li", class_=site.location_class).get_text(strip=True):
            return False
        # Check if the link element has a non-empty href attribute
        link_element = bs_element.find("a", class_=site.link_class)
        if link_element and not link_element.get("href", "").strip():
            return False
        # Add more checks as necessary for other elements
    except AttributeError:
        # AttributeError is raised if find() returns None (element not found)
        return False
    return True


def scroll_list(driver, site):
    for i in range(300, 6000, 100):
        driver.execute_script(
            "arguments[0].scrollTo(0, {})".format(i),
            driver.find_element(By.CLASS_NAME, site.search_results_list_class),
        )


def calculate_expected_results(total_results, current_page, search_results_per_page):
    if is_last_page(current_page, search_results_per_page, total_results):
        return total_results % search_results_per_page
    else:
        return search_results_per_page


def is_last_page(current_page, search_results_per_page, total_results):
    if (current_page * search_results_per_page) > total_results:
        return True
    else:
        return False


def extract_jobs_from_joblist(driver, driver_job_list, job_list, site):
    retry_count = 0
    max_retries = 5  # Set a limit for retries before asking for user input
    try:
        for index, job in enumerate(job_list):
            while True:
                try:
                    # Get a fresh reference to the link element on each attempt
                    link = driver_job_list[index].find_element(
                        By.CLASS_NAME, site.link_class
                    )
                    if is_selenium_element_loaded(driver_job_list[index]):
                        link.click()  # Click the link to load the job description
                        break  # Successful click, break out of the loop
                except NoSuchElementException as e:
                    # Element not found, will try again after scrolling
                    # Check if the retry limit is reached
                    if retry_count >= max_retries:
                        input(
                            f"Failed to scrape job description: {e}. Press Enter to try again or Ctrl+C to interrupt the process."
                        )
                        retry_count = 0  # Reset retry count after user input
                    else:
                        logging.info(
                            f"Retrying to scrape job description: {e}... Attempt {retry_count + 1}/{max_retries}"
                        )

                # Scroll and wait for a brief period to allow content to load
                scroll_list(driver, site)
                retry_count += 1
                time.sleep(1.5)
                driver_job_list = driver.find_elements(
                    By.CLASS_NAME, site.job_list_item_class
                )

            description_extraction_successful = False
            while not description_extraction_successful:
                try:
                    description_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, site.description_class)
                        )
                    )
                    description = description_element.text
                    description_extraction_successful = True
                except TimeoutException as e:
                    retry += 1
                    logging.error(f"Error loading description for job {index}: {e}")
                    if retry_count:
                        input(
                            f"Failed to load description. Press Return to retry or Ctrl+C to stop."
                        )
                        retry_count = 0
                    else:
                        logging.info(
                            f"Retrying... Attempt {retry_count + 1}/{max_retries}"
                        )

            while True:
                try:
                    # Re-fetch the page source for the specific job posting
                    page_source = BeautifulSoup(driver.page_source, "html.parser")
                    updated_job = page_source.find_all(
                        "li", class_=site.job_list_item_class
                    )[index]

                    # Attempt to find the required BeautifulSoup elements in the updated job
                    title_element = updated_job.find("a", class_=site.link_class)
                    company_name_element = updated_job.find(
                        "span", class_=site.company_name_class
                    )
                    location_element = updated_job.find(
                        "li", class_=site.location_class
                    )
                    link_element = updated_job.find("a", class_=site.link_class)

                    # If all elements are found, proceed to extract data
                    if all(
                        [
                            title_element,
                            company_name_element,
                            location_element,
                            link_element,
                        ]
                    ):
                        # Extract job details
                        title = title_element.get_text(strip=True)
                        company_name = company_name_element.get_text(strip=True)
                        location = location_element.get_text(strip=True)
                        link = link_element["href"]
                        job_id = updated_job["data-occludable-job-id"]

                        yield {
                            "title": title,
                            "company_name": company_name,
                            "location": location,
                            "link": link,
                            "id": job_id,
                            "description": description,
                        }
                        break  # Successfully extracted, break out of the loop
                except Exception as e:
                    retry_count += 1
                    # Log the exception for debugging
                    logging.warning(f"Encountered an issue: {e}")
                    if retry_count >= max_retries:
                        input(
                            f"Failed to extract job details. Press Return to retry or Ctrl+C to stop."
                        )
                        retry_count = 0
                    else:
                        logging.info(
                            f"Retrying... Attempt {retry_count + 1}/{max_retries}"
                        )

                # Scroll and wait for a brief period before retrying
                scroll_list(driver, site)
                time.sleep(1.5)
            time.sleep(1.5)
    except Exception as e:
        retry_count += 1
        logging.error(f"Failed to extract job details: {e}")
        if retry_count >= max_retries:
            input("Press Return to retry or Ctrl+C to stop.")
            retry_count = 0
        else:
            logging.info(f"Retrying... Attempt {retry_count + 1}/{max_retries}")


def extract_jobs_from_joblist_old(driver, driver_job_list, job_list, site):
    try:
        for index, job in enumerate(job_list):
            while True:
                try:
                    # Get a fresh reference to the link element on each attempt
                    link = driver_job_list[index].find_element(
                        By.CLASS_NAME, site.link_class
                    )
                    if is_selenium_element_loaded(driver_job_list[index]):
                        link.click()  # Click the link to load the job description
                        break  # Successful click, break out of the loop
                except NoSuchElementException:
                    # Element not found, will try again after scrolling
                    pass

                # Scroll and wait for a brief period to allow content to load
                scroll_list(driver, site)
                time.sleep(1.5)
                driver_job_list = driver.find_elements(
                    By.CLASS_NAME, site.job_list_item_class
                )

            try:
                description_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, site.description_class)
                    )
                )
                description = description_element.text
            except TimeoutException as e:
                logging.error(f"Error loading description for job {index}: {e}")
                input("Press Return to retry or Ctrl+C to stop.")
                continue  # Skip to the next job

            while True:
                try:
                    # Re-fetch the page source for the specific job posting
                    page_source = BeautifulSoup(driver.page_source, "html.parser")
                    updated_job = page_source.find_all(
                        "li", class_=site.job_list_item_class
                    )[index]

                    # Attempt to find the required BeautifulSoup elements in the updated job
                    title_element = updated_job.find("a", class_=site.link_class)
                    company_name_element = updated_job.find(
                        "span", class_=site.company_name_class
                    )
                    location_element = updated_job.find(
                        "li", class_=site.location_class
                    )
                    link_element = updated_job.find("a", class_=site.link_class)

                    # If all elements are found, proceed to extract data
                    if all(
                        [
                            title_element,
                            company_name_element,
                            location_element,
                            link_element,
                        ]
                    ):
                        # Extract job details
                        title = title_element.get_text(strip=True)
                        company_name = company_name_element.get_text(strip=True)
                        location = location_element.get_text(strip=True)
                        link = link_element["href"]
                        job_id = updated_job["data-occludable-job-id"]

                        yield {
                            "title": title,
                            "company_name": company_name,
                            "location": location,
                            "link": link,
                            "id": job_id,
                            "description": description,
                        }
                        break  # Successfully extracted, break out of the loop
                except Exception as e:
                    # Log the exception for debugging
                    logging.warning(f"Encountered an issue: {e}")

                # Scroll and wait for a brief period before retrying
                scroll_list(driver, site)
                time.sleep(1.5)
            time.sleep(1.5)
    except Exception as e:
        logging.error(f"Failed to extract job details: {e}")
        input("Press Return to retry or Ctrl+C to stop.")


def is_valid_url(url):
    # Regular expression for validating a URL
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:\S+(?::\S*)?@)?"  # user:pass authentication
        r"(?:"  # domain...
        r"(?:[A-Z\d](?:[A-Z\d-]{0,61}[A-Z\d])?\.)+"  # domain dot something
        r"(?:[A-Z]{2,6}\.?|[A-Z\d-]{2,}\.?)|"  # domain extension
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"  # ...or ipv4
        r"|\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # ...or ipv6
        r"(?::\d+)?"  # optional port
        r"(?:/\S*)?$",  # path
        re.IGNORECASE,
    )
    return re.match(regex, url) is not None


def get_new_filename(keyword, location, file_format, directory="./"):
    # Create a valid filename
    filename = f"{keyword}_({location})".replace(" ", "_")
    filename = re.sub(
        r"[^\w\s]", "", filename
    )  # Remove any non-alphanumeric characters

    existing_files = sorted(
        [f for f in os.listdir(directory) if f.startswith(filename)],
        reverse=True,  # Sort in descending order to handle the highest suffix first
    )

    # Rename existing files if necessary
    for file in existing_files:
        suffix_match = re.search(r"\.(\d+)$", file)
        if suffix_match:
            new_suffix = int(suffix_match.group(1)) + 1
            new_name = re.sub(r"\.\d+$", f".{new_suffix}", file)
            os.rename(os.path.join(directory, file), os.path.join(directory, new_name))

    # If the base file exists, rename it to .1
    base_filename = f"{filename}.{file_format}"
    if base_filename in existing_files:
        os.rename(
            os.path.join(directory, base_filename),
            os.path.join(directory, f"{filename}.1.{file_format}"),
        )

    return os.path.join(directory, base_filename)


def get_new_filename_old(keyword, location, file_format, directory="./"):
    # Create a valid filename
    filename = f"{keyword}_({location})".replace(" ", "_")
    filename = re.sub(
        r"[^\w\s]", "", filename
    )  # Remove any non-alphanumeric characters

    # Check for existing files and find the highest suffix number
    max_suffix = -1
    for file in os.listdir(directory):
        if file.startswith(filename) and file.endswith(file_format):
            suffix = re.search(r"\.(\d+)\." + re.escape(file_format) + "$", file)
            if suffix:
                max_suffix = max(max_suffix, int(suffix.group(1)))

    # Determine new filename
    if max_suffix == -1:
        new_filename = f"{filename}.{file_format}"
    else:
        new_filename = f"{filename}.{max_suffix + 1}.{file_format}"

    return os.path.join(directory, new_filename)


def save_file(data, filename):
    directory = os.path.dirname(filename)

    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save the file
    with open(filename, "w") as file:
        file_format = filename.split(".")[-1]
        if file_format == "json":
            import json

            json.dump(data, file)
        elif file_format == "csv":
            import csv

            writer = csv.writer(file)
            writer.writerows(
                data
            )  # Assuming data is a list of lists or similar iterable


class Job(BaseModel):
    title: str
    company_name: str
    location: str
    link: str
    id: str
    description: str


pages = 50
file_format = "json"
current_page = 1

driver = set_up_selenium()

# Define the required parameters
required_params = {"f_WT", "geoId", "location", "keywords"}

# Define the file path
file_path = "queries.txt"

# Check if the file exists
if not os.path.exists(file_path):
    logging.error("Error: 'queries.txt' does not exist.")
    exit(1)

# Read the URLs into a list
with open(file_path, "r") as file:
    queries = [line.strip() for line in file if line.strip()]

# Validate URLs and their parameters
for query in queries:
    if not is_valid_url(query):
        logging.error(f"Error: Invalid URL found in queries.txt - {query}")
        exit(1)
    parsed_url = urlparse(query)
    query_params = set(parse_qs(parsed_url.query).keys())
    if not required_params.issubset(query_params):
        logging.error(
            f"Error: The query misses required parameters: {required_params - query_params}"
        )
        exit(1)

# query = "https://www.linkedin.com/jobs/search/?f_WT=2&geoId=91000000&keywords=hr%20manager&location=European%20Union"

for index, query in enumerate(queries):
    # Extract the keywords parameter for the progress bar title
    parsed_url = urlparse(query)
    current_query_params = parse_qs(parsed_url.query)
    keywords = current_query_params.get("keywords", [""])[0].replace("%20", " ")
    location = current_query_params.get("location", [""])[0].replace("%20", " ")
    progress_bar_description = f"{keywords} ({location})"
    file_name = get_new_filename(keywords, location, file_format)

    site = LinkedIn(query)
    if index == 0:
        log_in(driver, site)

    total_results = prepare_search_results_page(driver, site, current_page)
    max_pages = total_results // 25 + (1 if total_results % 25 != 0 else 0)
    total_pages = min(pages, max_pages)
    max_results = total_pages * 25
    if total_pages < max_pages:
        total_results = min(max_results, total_results)

    jobs = []
    # Initialize the progress bar
    progress_bar = tqdm(total=total_results, desc=progress_bar_description)

    for page in range(1, total_pages + 1):
        if page < 1:
            site.update_query(page)
            prepare_search_results_page(driver, site, page)

        # Load search results for the current page
        driver_job_list, job_list = load_search_results(
            driver, site, total_results, page
        )

        for job in extract_jobs_from_joblist(driver, driver_job_list, job_list, site):
            jobs.append(job)
            # Update the progress bar with the number of processed jobs
            progress_bar.update(1)
            progress_bar.set_postfix_str(
                f"Processed Jobs: {len(jobs)} / {total_results}, Page: {page}/{total_pages}"
            )
            save_file(jobs, file_name)
        time.sleep(5)

    # Close the progress bar after all jobs are processed
    progress_bar.close()
    print("\033[92m" + f"Saved jobs to {file_name}" + "\033[0m")
    # User confirmation to proceed
    if index != len(queries) - 1:
        input("Press Return to continue to the next query, or Ctrl+C to stop.")
