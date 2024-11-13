# hoyo-code

English | [Indonesia](README_id.md)

![Cover](https://repository-images.githubusercontent.com/803866357/958bc2c1-1703-4127-920c-853291495bdc)

## Introduction

This project is a Python 3 tool designed to scrape promotional or redeem codes from Wiki Fandom pages for Hoyoverse games, including **Genshin Impact**, **Honkai Star Rail**, and **Honkai Impact 3rd**. The scraper retrieves active and expired redeem codes and is automated to run at regular intervals using GitHub Actions, ensuring the latest codes are always available.

## Features

-   [x] **Automatic Code Scraping**: Pulls the latest promotional codes from Fandom Wiki pages.
-   [x] **Supported Games**: Genshin Impact, Honkai Star Rail, Honkai Impact 3rd.
-   [x] **Automated Updates**: Scheduled GitHub Actions workflow to automatically run the scraper and update code lists.
-   [x] **Easy-to-use**: Fetches and displays codes in json & txt format for easy use.

## Upcoming Features

-   [ ] **Supported Games**: Zenzenles Zone Zero.

## Requirements

-   Python 3.12+
-   `requests` for making HTTP requests
-   `beautifulsoup4` for HTML parsing

To install the required packages, run:

```bash
pip install -r requirements.txt
```

## Setup

### 1. Clone the repository:

```bash
git clone https://github.com/haiueom/hoyo-code.git
cd hoyo-code
```

### 2. Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure the repository to use GitHub Actions for automation (instructions below).

## Usage

To run the scraper manually:

```bash
python main.py
```

This will fetch the latest redeem codes and display them in the console or save them in a text file (codes.txt) for easy access.

## Automation with GitHub Actions

The GitHub Actions workflow is set up to automate the scraping process and update the list of codes on a regular schedule (e.g., daily).

### 1. Enabling GitHub Actions

1. In your repository, go to **Actions**.
2. Make sure Actions are enabled.

### 2. GitHub Actions Workflow

The `.github/workflows/scraper.yml` file is already included to define the automation schedule and steps. By default, the scraper runs daily at midnight or you can change the cronjobs time as you like.

> [!IMPORTANT]
> The max frequency of cronjobs on GitHub actions is every 5 minutes.

```yaml
name: Hoyoverse Code Scraper

on:
    schedule:
        - cron: "0 0 * * *" # Runs daily at midnight
    workflow_dispatch:

jobs:
    scrape-codes:
        runs-on: ubuntu-latest
        steps:
            - name: Check out the repository
              uses: actions/checkout@v2

            - name: Set up Python
              uses: actions/setup-python@v2
              with:
                  python-version: "3.x"

            - name: Install dependencies
              run: |
                  python -m pip install --upgrade pip
                  pip install -r requirements.txt

            - name: Run the scraper
              run: python scraper.py

            - name: Commit and push changes
              run: |
                  git config --local user.name "github-actions[bot]"
                  git config --local user.email "github-actions[bot]@users.noreply.github.com"
                  git add .
                  git commit -m "Automated code update $(date +'%Y-%m-%d')"
                  git push
```

This workflow will:

1. Check out the repository.
2. Set up Python.
3. Install dependencies.
4. Run the scraper.
5. Commit and push any changes to the repository.

## Contributing

1. Fork the repository.
2. Create your feature branch (git checkout -b feature/YourFeature).
3. Commit your changes (git commit -m 'Add YourFeature').
4. Push to the branch (git push origin feature/YourFeature).
5. Open a pull request.

## Support

## License

This project is licensed under the [MIT License](LICENSE).
