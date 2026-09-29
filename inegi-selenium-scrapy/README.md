# INEGI Sanctions Scraper (Selenium + Scrapy)

Automated scraper that collects **sanctioned suppliers ("proveedores sancionados")** from the official [INEGI website](https://www3.inegi.org.mx/sistemas/ci/relps/) using **Selenium** and **Scrapy**, and updates a structured JSON file (`sanctions.json`) every hour via **GitHub Actions**.

---

## Overview

This project automates the extraction of public sanction data published by INEGI (Mexico’s National Institute of Statistics and Geography).  
The spider navigates dynamically rendered content using Selenium, extracts supplier names and sanction numbers, and outputs them as clean, structured JSON.

Every hour, the scraper runs automatically on **GitHub Actions**, regenerates the JSON file, and commits it back to the repository if any updates are detected.

---

## Project Structure

inegi/<br />
└── .github/<br />
│    └── workflows/<br />
│    &nbsp; &nbsp; └── run_scraper.yml # GitHub Actions automation<br />
│<br />
├── inegi/<br />
│ ├── spiders/<br />
│ │ └── inegi_spider.py # Main Scrapy spider (with Selenium logic)<br />
│ │ <br />
│ ├── items.py # Defines scraped item structure<br />
│ ├── middlewares.py<br />
│ ├── pipelines.py # Saves and formats JSON output<br />
│ └── settings.py # Scrapy configuration<br />
│<br />
├──.gitignore<br />
├──README.md<br />
├──flowchart_inegi_.jpg<br /> 
├──main.py # Script to run the spider locally<br />
├──requirements.txt<br />
├──sanctions.json # Automatically updated data output<br />
├──scraper.yaml # Target URL and search parameters<br />
└──scrapy.cfg # Scrapy project configuration<br />


## How It Works<br />

1. **Selenium** launches a headless Chrome browser and loads the INEGI sanctions page.  
2. The spider searches for the configured term (from `scraper.yaml`), e.g. `"Ver total de proveedores sancionados"`.
3. Each sanction record is opened and parsed, extracting:
   - Entity name (`Entity_name`)
   - Sanction number(s) (`Sanction_numbers`)
4. **Scrapy Pipelines** save all results into a formatted JSON file:
   ```json
   [
     {
       "last_updated": "2025-11-02 10:45:11 UTC"
     },
     {
       "Entity_name": "ASHANTY FERNANDEZ MARTINEZ",
       "Sanction_numbers": ["40.902.05/8/2013"]
     }
   ]


5.GitHub Actions runs every hour, regenerates the file, and commits it automatically.<br />

## Requirements<br />

Python ≥ 3.10<br />
Google Chrome + ChromeDriver (for local runs)<br />

Dependencies:<br />
pip install scrapy selenium pyyaml<br />

# Run the spider manually<br />
python main.py<br />

## GitHub Actions Automation<br />

The workflow file .github/workflows/run_scraper.yml runs daily:<br />

on:<br />
  schedule:<br />
    - cron: "0 0 * * *"<br />
  workflow_dispatch:<br />


# Each run:<br />

Sets up Python<br />
Installs dependencies<br />
Runs the scraper in headless mode<br />
Updates sanctions.json<br />
Commits and pushes updates back to the main branch<br />

## Failure Alert (Email Notification)<br />

This project includes an automated email alert system. If the scraper fails during execution (e.g. site structure changes, Selenium errors, or runtime exceptions),
a notification email is automatically sent via GitHub Actions to inform maintainers immediately.

This ensures rapid awareness of parsing issues and improves operational reliability.
