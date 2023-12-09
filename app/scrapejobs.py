import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from urllib.parse import urlencode, urlparse, parse_qs
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pandas as pd
import argparse
from tqdm import tqdm
import logging
import re

"""
LinkedIn Job Scraper

Overview:
This script scrapes job listings from LinkedIn. It automates gathering job posting data, handles LinkedIn's verification prompts, and saves the data in a structured format.

Usage:
- Run via command line with arguments for job title, geographical area, remote preference, and experience level.
- Optional LinkedIn search URL (-q/--query_url) overrides individual search parameters.
- Exports data in JSON or CSV formats.
- Retries on incomplete page loads; saves data before terminating on terminal errors.

Command Line Arguments:
- -j/--job_title: Job title to search for.
- -g/--geography: Geographical area (e.g., 'european-union', 'united-states').
- -r/--remote: Remote job preference (e.g., 'remote', 'on-site').
- -e/--experience: Experience level required (e.g., 'entry-level', 'mid-senior-level').

- -p/--page_count: Number of pages to scrape.
- -d/--directory: Directory to save the data file.
- -f/--format: File format (JSON or CSV).

- -q/--query_url: LinkedIn search URL (optional).

Note:
- Requires user intervention post-login for LinkedIn verification.

Example:
`python scrapejobs.py -j "Data Engineer" -g "european-union" -r "remote" -p 5 -d "./data" -f "csv"`
Or
`python scrapejobs.py -q "<LinkedIn search URL>" -p 5 -d "./data" -f "csv"`
"""

TO_JSON = "json"
TO_CSV = "csv"

# ANSI escape sequences for colors
CYAN = "\033[36m"
RESET = "\033[0m"


def debug_cyan(message):
    logger.debug(f"{CYAN}{message}{RESET}")


# Logger configuration
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)
# logging.basicConfig(
#     level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
# )

logger = logging.getLogger(__name__)


def debug_cyan(message):
    logger.debug(f"{CYAN}{message}{RESET}")


class WebNavigator:
    """
    A web navigator class that interacts with a website using Selenium WebDriver.

    Args:
        site: The site object representing the website to navigate.
        query: The query details.

    Attributes:
        driver: The Selenium WebDriver instance.
        site: The site object representing the website being navigated.
        query: The query details.

    Methods:
        __init__(self, site, query): Initializes the WebNavigator with a site object and query details.
        login(self): Logs into the site using provided credentials.
        accept_cookies(self, cookie_button_xpath): Accepts cookies if the button is present.
        wait_for_manual_verification(self): Waits for manual verification on LinkedIn.
        search_results(self, start): Navigates to the search results page and scrolls to load all job postings.
        open_post(self, job_link): Opens a job posting and clicks 'See more' if necessary.
        safe_get(self, url, retries=3): Safely gets the URL, retrying a specified number of times in case of network issues.
        page_source(self): Returns the current page source as a BeautifulSoup object.
        quit(self): Quits the browser.
    """

    def __init__(self, site, query):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.site = site
        self.query = query
        self.login()

    def login(self):
        """
        Logs into the website using the provided credentials.

        This function performs the following steps:
        1. Navigates to the login URL of the website.
        2. Waits for 2 seconds to ensure the page is loaded.
        3. Accepts cookies if the cookies button is present.
        4. Enters the email and password in the respective fields.
        5. Clicks on the login button.
        6. If the login URL is for LinkedIn, waits for manual verification.

        Raises:
            WebDriverException: If the login process fails.

        Returns:
            None
        """
        self.safe_get(self.site.login_url)
        time.sleep(2)

        try:
            self.accept_cookies(self.site.cookie_button_xpath())
        except NoSuchElementException:
            pass

        try:
            self.driver.find_element(By.ID, "username").send_keys(self.site.email)
            self.driver.find_element(By.ID, "password").send_keys(self.site.password)
            self.driver.find_element(By.XPATH, self.site.login_button_xpath()).click()
            if self.site.login_url == "https://www.linkedin.com/login":
                logger.info("LinkedIn!")
                self.wait_for_manual_verification()
        except WebDriverException:
            logger.error("Login failed. Please check your credentials.")
            exit(1)

    def accept_cookies(self, cookie_button_xpath):
        """
        Clicks on the accept cookies button if it exists.

        Args:
            cookie_button_xpath (str): The XPath of the accept cookies button.

        Returns:
            None
        """
        try:
            cookie_button = self.driver.find_element(By.XPATH, cookie_button_xpath)
            cookie_button.click()
        except:
            pass

    def wait_for_manual_verification(self):
        input(
            "Please complete the LinkedIn verification and then press Enter to continue..."
        )

    def search_results(self, start):
        """
        Searches for job results based on the provided start index.

        Args:
            start (int): The index of the first job result to retrieve.

        Returns:
            None

        Raises:
            TimeoutException: If the page does not load within the specified time.
            WebDriverException: If there is an issue with the web driver.

        """
        try:
            if self.query.query_url:
                parsed_url = urlparse(self.query.query_url)
                original_query_params = parse_qs(parsed_url.query)

                # Log original parameters
                debug_cyan(f"Original query params: {original_query_params}")

                # Create a new dictionary excluding 'currentJobId' and 'start'
                query_params = {
                    k: v
                    for k, v in original_query_params.items()
                    if k not in ["currentJobId", "start"]
                }

                # Log modified parameters
                debug_cyan(
                    f"Modified query params (before adding 'start'): {query_params}"
                )

                # Add the 'start' parameter based on the current page
                query_params["start"] = [str(start)]

                # Log final parameters
                debug_cyan(f"Final query params (after adding 'start'): {query_params}")

                # Reconstruct the URL with updated parameters
                final_url = parsed_url._replace(
                    query=urlencode(query_params, doseq=True)
                ).geturl()

                # Log the final URL for verification
                logger.info(f"Final URL: {final_url}")

                # Log the final URL
                debug_cyan(f"Final URL: {final_url}")

            else:
                params = urlencode(
                    {
                        "keywords": self.query.job_title,
                        "geoId": self.query.geography,
                        "f_WT": self.query.remote,
                        "start": start,
                        "f_E": self.query.experience,
                    }
                )
                final_url = f"https://www.linkedin.com/jobs/search/?{params}"
            self.safe_get(final_url)

            job_list_container = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, self.site.job_list_container())
                )
            )

            scrollresults = self.driver.find_element(
                # By.CLASS_NAME, "jobs-search-results-list"
                By.CLASS_NAME,
                self.site.search_results_list(),
            )
            time.sleep(1)

            # Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
            for i in range(300, 3000, 100):
                self.driver.execute_script(
                    "arguments[0].scrollTo(0, {})".format(i), scrollresults
                )
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Error navigating to the page: {e}")

    # Returns the current page source as a BeautifulSoup object
    def page_source(self):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        return soup

    def open_post(self, job_link):
        """
        Retrieves the page source of the current web page.

        :param self: The instance of the class.
        :return: A BeautifulSoup object representing the parsed HTML of the page source.
        """
        clickable_element = self.driver.find_element(
            By.XPATH, f"//a[@href='{job_link}']"
        )
        self.driver.execute_script("arguments[0].scrollIntoView();", clickable_element)
        clickable_element.click()
        time.sleep(1)
        try:
            see_more_button = self.driver.find_element(
                By.CLASS_NAME, self.site.see_more_button()
            )
            if see_more_button.is_displayed():
                see_more_button.click()
                time.sleep(1)
        except:
            pass

    def re_scroll(self):
        scrollresults = self.driver.find_element(
            By.CLASS_NAME, self.site.search_results_list()
        )

        for i in range(300, 3000, 100):
            self.driver.execute_script(
                "arguments[0].scrollTo(0, {})".format(i), scrollresults
            )

    def safe_get(self, url, retries=3):
        """
        Retrieves the specified URL safely by handling exceptions and retries.

        Args:
            url (str): The URL to retrieve.
            retries (int, optional): The number of times to retry in case of network issues. Defaults to 3.

        Raises:
            TimeoutException: If the page load timeout is reached.
            WebDriverException: If there is an issue with the web driver.

        Returns:
            None: If the URL is successfully retrieved.

        """
        attempt = 0
        while attempt < retries:
            try:
                self.driver.get(url)
                return  # Exit the function if successful
            except (TimeoutException, WebDriverException) as e:
                attempt += 1
                if attempt == retries:
                    raise  # Reraising the exception after all retries have failed
                logger.error(
                    f"Network issue encountered. Retrying {attempt}/{retries}..."
                )
                time.sleep(5)  # Wait for some time before retrying

    # Quits the browser
    def quit(self):
        self.driver.quit()


class LinkedIn:
    """
    Defines LinkedIn-specific configurations and provides methods for interacting with the LinkedIn website.

    Functions:
    - __init__(): Initializes the LinkedIn class and sets the login URL, email, and password.
    - cookie_button_xpath(): Returns the xpath for the cookie button on the LinkedIn login page.
    - login_button_xpath(): Returns the xpath for the login button on the LinkedIn login page.
    - set_geography(geography): Maps the input geography to its corresponding value and returns it.
    - set_remote(remote): Maps the input remote option to its corresponding value and returns it. If no match is found, it returns the default value "1,2,3".
    - job_list_container(): Returns the class name of the job list container element on the LinkedIn jobs search page.
    - job_list_item(): Returns the class name of the job list items on the LinkedIn jobs search page.
    - search_results_list(): Returns the class name of the search results list on the LinkedIn jobs search page.
    - job_title(): Returns the class name of the job title element on the LinkedIn job details page.
    - company_name(): Returns the class name of the company name element on the LinkedIn job details page.
    - location(): Returns the class name of the location element on the LinkedIn job details page.
    - job_link(): Returns the class name of the job link element on the LinkedIn job details page.
    - see_more_button(): Returns the class name of the "See More" button on the LinkedIn job details page.
    - job_description(): Returns the class name of the job description element on the LinkedIn job details page.
    - base_url(): Returns the base URL of the LinkedIn website.
    """

    def __init__(self):
        self.login_url = "https://www.linkedin.com/login"
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")

    def cookie_button_xpath(self):
        """
        Returns the XPath for the cookie button on the LinkedIn webpage.

        :param self: The instance of the class.
        :return: The XPath string for the cookie button.
        """
        xpath = "/html/body/div/main/div[1]/div/section/div/div[2]/button[2]"
        return xpath

    def login_button_xpath(self):
        xpath = '//*[@id="organic-div"]/form/div[3]/button'
        return xpath

    def set_geography(self, geography):
        geography_mappings = {
            "european-union": "91000000",
            "united-states": "103644278",
        }
        return geography_mappings.get(
            geography.lower(), "91000000"
        )  # Default to "european-union" if not matched
        # if geography == "European Union":
        #     return 91000000
        # if geography == "United States":
        #     return 103644278

    def set_remote(self, remote):
        remote_mappings = {
            "on-site": "1",
            "remote": "2",
            "hybrid": "3",
            "on-site-or-remote": "1,2",
            "on-site-or-hybrid": "1,3",
            "hybrid-or-remote": "2,3",
            "any": "1,2,3",
        }
        return remote_mappings.get(
            remote.lower(), "1,2,3"
        )  # Default to "any" if not matched

    def set_experience(self, experience):
        # If experience is a valid string, use it; otherwise, default to "1,2,3,4,5,6"
        return (
            experience if self.is_valid_experience_input(experience) else "1,2,3,4,5,6"
        )

    def is_valid_experience_input(self, input_string):
        # Regex pattern to match the specified format for the experience parameter
        pattern = r"^(?:[1-6](?:,[1-6]){0,5})$"

        # Check if the input matches the regex pattern
        if re.match(pattern, input_string):
            numbers = set(input_string.split(","))

            # Ensure all numbers are unique and in the range 1-6
            return all(num in {"1", "2", "3", "4", "5", "6"} for num in numbers)

        return False

    """
    The following methods return the class names of the
    corresponding elements on the LinkedIn job details page.
    """

    def job_list_container(self):
        container = "scaffold-layout__list"
        return container

    def job_list_item(self):
        item = "jobs-search-results__list-item"
        return item

    def search_results_list(self):
        list = "jobs-search-results-list"
        return list

    def job_title(self):
        title = "job-card-list__title"
        return title

    def company_name(self):
        name = "job-card-container__primary-description"
        return name

    def location(self):
        location = "job-card-container__metadata-item"
        return location

    def job_link(self):
        link = "job-card-container__link"
        return link

    def see_more_button(self):
        button = "jobs-description__footer-button"
        return button

    def job_description(self):
        description = "jobs-description-content__text"
        return description

    def base_url(self):
        url = "https://www.linkedin.com"
        return url


class Query:
    def __init__(
        self, site, job_title="", geography="", remote="", experience="", query_url=""
    ):
        self.site = site
        # Initialize attributes with default values
        self.job_title = job_title
        self.geography = geography
        self.remote = remote
        self.experience = experience

        if query_url:
            self.query_url = query_url
            self.extract_parameters_from_url()
        else:
            self.geography = site.set_geography(geography)
            self.remote = site.set_remote(remote)
            self.experience = site.set_experience(experience)

    def extract_parameters_from_url(self):
        parsed_url = urlparse(self.query_url)
        query_params = parse_qs(parsed_url.query)

        # Update attributes from URL parameters if available
        self.job_title = query_params.get("keywords", [self.job_title])[0]
        self.geography = query_params.get("geoId", [self.geography])[0]
        self.remote = query_params.get("f_WT", [self.remote])[0]
        self.experience = query_params.get("f_E", [self.experience])[0]


class Job:
    # Represents a single job posting with its details
    def __init__(
        self, job_title, company_name, location, job_link, job_id, job_description
    ):
        self.job_title = job_title
        self.company_name = company_name
        self.location = location
        self.job_link = job_link
        self.job_id = job_id
        self.job_description = job_description


def save_to_file(jobs, query, args):
    # Saves the scraped data to a CSV or JSON file
    job_dicts = [job.__dict__ for job in jobs]
    df = pd.DataFrame(job_dicts)

    # Saves the scraped data to a CSV or JSON file
    job_title = query.job_title.replace(" ", "_")
    geography = query.geography.replace(" ", "_")
    remote = query.remote.replace(" ", "_")
    base_name = f"jobs_{job_title}_-_{geography}_-_{remote}_-_LinkedIn"
    file_format = args.format
    file_extension = f".{file_format}"
    final_path = rename_existing_file(args.directory, base_name, file_extension)

    # Save DataFrame to file based on the specified format
    if file_format == TO_JSON:
        df.to_json(final_path, orient="records", lines=True)
    elif file_format == TO_CSV:
        df.to_csv(final_path, index=False)
    print(f"\033[92mData saved to {final_path}\033[0m")


def rename_existing_file(base_path, base_name, file_extension):
    # Renames an existing file if it exists to avoid overwriting
    final_path = os.path.join(base_path, base_name + file_extension)
    if os.path.exists(final_path):
        counter = 1
        new_name = f"{base_name}({counter}){file_extension}"
        while os.path.exists(os.path.join(base_path, new_name)):
            counter += 1
            new_name = f"{base_name}({counter}){file_extension}"
        os.rename(final_path, os.path.join(base_path, new_name))
    return final_path

def main():
    # Main argument parser
    parser = argparse.ArgumentParser(description="Job scraper")
    parser.add_argument("-q", "--query_url", type=str, help="LinkedIn query URL.")

    # Conditional requirement for the job title
    parser.add_argument(
        "-j", "--job_title", type=str, required=False, help="Job title to search for."
    )

    # parser.add_argument(
    #     "-s",
    #     "--site",
    #     type=str,
    #     default="linkedin",
    #     choices=["linkedin"],
    #     help='Site to scrape. Currently only supports "linkedin".',
    # )

    parser.add_argument(
        "-g",
        "--geography",
        type=str,
        default="european-union",
        choices=["european-union", "united-states"],
        help='Geographical area for the job search. Default is "european-union".',
    )
    parser.add_argument(
        "-r",
        "--remote",
        type=str,
        default="any",
        choices=[
            "on-site",
            "remote",
            "hybrid",
            "on-site-or-hybrid",
            "on-site-or-remote",
            "any",
        ],
        help="Specify the work type preference: on-site, remote, hybrid, on-site-or-hybrid, on-site-or-remote, any. Default is 'any'.",
    )
    parser.add_argument(
        "-p",
        "--page_count",
        type=int,
        default=5,
        help="Number of pages to scrape. Default is 5.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default="",
        help="File path where the JSON file will be saved. Default is the current directory.",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=[TO_JSON, TO_CSV],
        default=TO_JSON,
        help="Format of the output file. Can be either 'csv' or 'json'. Default is 'json'.",
    )
    parser.add_argument(
        "-e",
        "--experience",
        type=str,
        default="1,2,3,4,5,6",
        help='Specify the required experience: internship ("1"), entry-level ("2"), associate ("3"), mid-senior-level ("4"), director ("5"), executive ("6"). Combine experience levels separated by commas (lowest level first. E.g., "1,2,3"). Default is "1,2,3,4,5,6".',
    )

    # Parse the arguments
    args = parser.parse_args()

    # Additional logic to make job_title required if query_url is not provided
    if not args.query_url and not args.job_title:
        parser.error(
            "the following arguments are required: -j/--job_title when -q/--query_url is not provided"
        )

    load_dotenv()
    site = LinkedIn()
    query = Query(
        site=site,
        job_title=args.job_title,
        geography=args.geography,
        remote=args.remote,
        experience=args.experience,
        query_url=args.query_url,  # Assuming you've added an argument for query_url
    )
    navigator = WebNavigator(site=site, query=query)
    page_count = args.page_count

    index = 0
    total_jobs = page_count * 25  # Assuming each page has 25 jobs
    jobs = []
    with tqdm(
        total=total_jobs,
        desc=f"Page 1 out of {page_count}, 0 Jobs out of {total_jobs}",
        unit="job",
    ) as pbar:
        # with tqdm(total=page_count, desc="Scraping Pages", unit="page") as page_pbar:
        for page_num in range(1, page_count + 1):
            start = (page_num - 1) * 25
            navigator.search_results(start)

            page_source = navigator.page_source()

            job_postings = page_source.find_all("li", class_=site.job_list_item())
            num_job_postings = len(job_postings)
            logger.info(f"Number of job postings found: {len(page_source)}")

            search_result_list = page_source.find(
                "div", class_=site.search_results_list()
            )

            # Check if search_result_list is not None and re-scroll if necessary
            if search_result_list is None:
                logger.warning("Initial search results not found, re-scrolling...")
                navigator.re_scroll()
                page_source = navigator.page_source()
                search_result_list = page_source.find(
                    "div", class_=site.search_results_list()
                )

                # If still None after re-scrolling
                if search_result_list is None:
                    logger.error(
                        "Failed to find search results after re-scrolling."
                    )
                    continue  # Skip to the next page

            for item in search_result_list.find_all(
                "li", class_=site.job_list_item()
            ):
                logger.info(f"Processing job {index + 1}")

                try:
                    job_title_element = item.find("a", class_=site.job_title())
                    if job_title_element is None:
                        logger.error("Re-scrolling to load job posting")
                        navigator.re_scroll()
                        page_source = navigator.page_source()
                        search_result_list = page_source.find(
                            "div", class_=site.search_results_list()
                        )
                        job_list_items = search_result_list.find_all(
                            "li", class_=site.job_list_item()
                        )
                        if len(job_list_items) < index + 1:
                            logger.error(
                                "No job title found. Skipping to the next page."
                            )
                            break
                        item = search_result_list.find_all(
                            "li", class_=site.job_list_item()
                        )[index]
                        job_title_element = item.find(
                            "a", class_=site.job_title()
                        )
                        if job_title_element is None:
                            logger.error(
                                "No job title found. Skipping to the next page."
                            )
                            break
                    job_title = job_title_element.text.strip()
                    logger.info(f"Job title: {job_title}")
                    company_name = item.find(
                        "span", class_=site.company_name()
                    ).text.strip()
                    logger.info(f"Company name: {company_name}")
                    location = item.find(
                        "li", class_=site.location()
                    ).text.strip()
                    logger.info(f"Location: {location}")
                    job_link = item.find("a", class_=site.job_link())["href"]
                    logger.info(f"Job link: {job_link}")
                    job_id = job_link.split("/view/")[1].split("/")[0]
                    logger.info(f"Job ID: {job_id}")

                    navigator.open_post(job_link)
                    page_source = navigator.page_source()

                    job_description_element = page_source.find(
                        "div", class_=site.job_description()
                    )
                    if job_description_element is None:
                        logger.error(
                            "No job description found. Skipping to the next page."
                        )
                        break
                    job_description = job_description_element.text.strip()
                    job_link = site.base_url() + job_link
                    job = Job(
                        job_title,
                        company_name,
                        location,
                        job_link,
                        job_id,
                        job_description,
                    )
                    jobs.append(job)
                except (TimeoutException, WebDriverException) as e:
                    logger.error(f"Error generating job post: {e}")
                    save_to_file(jobs, query, args)
                    return  # Exit the program
                pbar.set_description(
                    f"Page {page_num} out of {page_count}, {len(jobs)} Jobs out of {total_jobs}"
                )
                pbar.update(1)
                logger.info("========")
                index += 1

    save_to_file(jobs, query, args)
    navigator.quit()


if __name__ == "__main__":
    main()
