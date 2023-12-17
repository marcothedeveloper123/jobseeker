# JobSeeker Project

## Overview

1. Recruiter AIs scan your résumé for keywords. If they don’t find the keywords, they discard your application. Let’s increase your chances at landing the job :)
2. When you do get invited for an interview, you are bound to bump into the question "What is your expected salary?" Most of us have no idea what to answer. Let's give you a leg up!

## Our customer

We do this project for the mythical Job Seeker

## Our job types

- Data Engineer
- AI Application Developer
- AI Strategy Consultant

## Features

- Scraping job postings
  - use something like [apify.com](https://apify.com/bebity/linkedin-jobs-scraper?cmdf=linkedin+job-search-api)
  - do the scraping ourselves
- Identifying skills gaps in resumes
- Providing salary range information

## Data Ingestion/Curation - [Medallion Architecture reference](https://www.databricks.com/glossary/medallion-architecture)

- Bronze Folder = Raw data sets labeled by sources. i.e. Data ingested using Apify from linkedin is stored at - bronze/apify/linkedin
- Silver Folder = Cleansed and conformed data. i.e. Data ingested using Apify from linkedin is transformed to contain the information we want to utilize to potentially assist job seekers, such as Job description, title, location, etc...
- Gold Folder = Curated solution ready data. i.e. Data cleaned and conformed that is ready to be used for providing insights to job seekers on improving their resume or skills to be more desirable in the job market.

## Contribution

Your contributions are welcome! Here's how you can help:

- **Suggest Ideas**: Open an 'issue' on our GitHub page and mention it's a suggestion.
- **Report Bugs**: Found a problem? Share it the same way and describe what you found.
- **Make Changes**: Want to fix or add something? 
  - Fork our project (this makes a copy).
  - Make your changes in your copy.
  - Send a 'pull request' so we can review and add your changes to the project.
  
Don't worry if you're new to this – we appreciate your help and are happy to guide you along the way!

## `scrapejobs.py` Documentation

### `scrapejobs.py` Overview

`scrapejos.py` is designed to automate the process of extracting job listings from LinkedIn based on user-provided search queries. It is built to handle the dynamic nature of web scraping with strategic user interventions to ensure stability and compliance with site interactions.

### Prerequisites

- **Chrome for Testing**: The script requires Chrome for Testing. You can download it from the [Chrome Availability Dashboard](https://googlechromelabs.github.io/chrome-for-testing/#stable).
- **Python Environment**: Ensure Python is installed on your system.
- **LinkedIn Account**: You need a LinkedIn account to perform searches.

### Setup Instructions

1. **Clone the Repository**: Clone this repository to your local machine.
2. **Install Dependencies**: Run `pip install -r requirements.txt` to install required Python modules.
3. **Chrome Driver**: Make sure you have the Chrome Driver installed and its path correctly set up in your system, which the script expects you to do in the constant `CHROME_BINARY_LOCATION`.

## Configuration

- **Environment File**: Rename `example.env` to `.env` and fill in your LinkedIn credentials.
- **Queries File**: Add your LinkedIn search queries to `queries.txt` in the root folder of the repository. Remove any '&origin=SWITCH_SEARCH_VERTICAL` and `currentJobId=xxxxxxxxxx&` from the URLs. Ensure each query contains the following parameters:
  - `f_WT`
  - `geoId`
  - `location`
  - `keywords`
- **Custom Settings**:
  - `pages`: Set the number of result pages to scrape.
  - `file_format`: Choose the file format for saving data (`json` or `csv`).

## Running the Script

- Execute the script via the command line. User intervention may be required:
  1. After login, to verify captcha if prompted.
  2. To handle scraping anomalies and repeated failures.

## Generating Requirements.txt

Run `pip freeze > requirements.txt` in your project directory to generate a list of all installed Python modules used in the project.

### Additional Information

- **Data Persistence**: The script saves data incrementally to avoid data loss during the scraping process.
- **Error Handling**: Log messages are color-coded for better readability. Red for errors, green for successful operations.
- **User Confirmation**: The script pauses for user confirmation after processing each query and upon encountering data extraction errors.

## Contribution Guidelines

Feel free to contribute to this project by submitting pull requests or opening issues for bugs or feature requests.
