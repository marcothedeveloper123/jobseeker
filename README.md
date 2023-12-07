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

## LinkedIn Job Scraper

### Overview
This script automates the process of scraping job listings from LinkedIn. It is designed to gather job posting data efficiently. The script handles LinkedIn's verification prompts and exports the data in a structured format.

### Usage
Run the script via the command line with parameters for job title, geographical area, remote preference, experience level, and more. It supports exporting data in JSON or CSV formats and has features to retry on incomplete page loads and save data before terminating on terminal errors.

#### Command Line Arguments
- `-j/--job_title`: Job title to search for.
- `-g/--geography`: Geographical area (e.g., 'european-union', 'united-states').
- `-r/--remote`: Remote job preference (e.g., 'remote', 'on-site').
- `-e/--experience`: Experience level required (e.g., 'entry-level', 'mid-senior-level').
- `-p/--page_count`: Number of pages to scrape.
- `-d/--directory`: Directory to save the data file.
- `-f/--format`: File format (JSON or CSV).
- `-q/--query_url`: LinkedIn search URL (optional).

### Examples
Run with individual parameters:
`python scrapejobs.py -j "Data Engineer" -g "european-union" -r "remote" -p 5 -d "./data" -f "csv"`
Or use a LinkedIn search URL:
`python scrapejobs.py -q "<LinkedIn search URL>" -p 5 -d "./data" -f "csv"`

## Note
This script requires user intervention post-login for LinkedIn verification. 