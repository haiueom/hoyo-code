# hoyo-code

English | [Indonesia](README_id.md)

![hoyo-code](https://github.com/user-attachments/assets/ca854ff0-ebfb-4f5f-80b5-67360f6156f9)

## Introduction

This project is a Python 3 tool designed to scrape promotional or redeem codes from Wiki Fandom pages for Hoyoverse games. The scraper retrieves active and expired redeem codes and is automated to run at regular intervals using GitHub Actions, ensuring the latest codes are always available.

## Features

-   [x] **Automatic Code Scraping**: Pulls the latest promotional codes from Fandom Wiki pages.
-   [x] **Supported Games**: Genshin Impact, Honkai Star Rail, Honkai Impact 3rd.
-   [x] **Automated Updates**: Scheduled GitHub Actions workflow to automatically run the scraper and update code lists.
-   [x] **Easy-to-use**: Fetches and displays codes in json & txt format for easy use.

## Upcoming Features

-   [ ] **Supported Games**: Zenzenles Zone Zero.

## Requirements

-   Python 3.12+

## Usage

### 1. Clone the repository:

```bash
git clone https://github.com/haiueom/hoyo-code.git
cd hoyo-code
```

### 2. Install the dependencies:

Dependencies used in this project:

-   `requests` for making HTTP requests
-   `beautifulsoup4` for HTML parsing

To install all required pip dependencies:

```bash
pip install -r requirements.txt
```

### 3. Run scrapper

To run the scraper manually:

```bash
python main.py
```

This will fetch the latest redeem codes and save them in json & text files.

## Automation with GitHub Actions

The GitHub Actions workflow is set up to automate the scraping process and update the list of codes on a regular schedule (e.g., daily).

### 1. Enabling GitHub Actions

1. In your repository, go to **Actions**.
2. Make sure Actions are enabled.

### 2. GitHub Actions Workflow

The `.github/workflows/scraper.yml` file is already included to define the automation schedule and steps. You can change the cronjobs time as you like.

> [!IMPORTANT]
> The max frequency of cronjobs on GitHub actions is every 5 minutes.

```yaml
name: Hoyoverse Code Scraper

on:
    schedule:
        - cron: "0 0 * * *" # you can change this
    workflow_dispatch:

scrape-codes:
    runs-on: ubuntu-latest
    permissions:
        contents: write
    steps:
        - name: checkout repository
          uses: actions/checkout@v4
        - name: setup python
          uses: actions/setup-python@v5
          with:
              python-version: 3.12.x
              cache: "pip"
        - name: install dependencies
          run: |
              python -m pip install --upgrade pip
              pip install -r requirements.txt
        - name: run the scraper
          run: |
              python main.py
        - name: commit and push changes
          run: |
              git config --local user.name "github-actions[bot]"
              git config --local user.email "github-actions[bot]@users.noreply.github.com"
              git add .

              # Check if there are changes
              if ! git diff-index --quiet HEAD; then
              git commit -m "update: $(date +'%Y-%m-%d')"
              git push
              else
              echo "No changes to commit"
              fi
```

## Support This Project

If you find this project useful and would like to support its development, consider:

-   **Starring the repository**: This helps others find the project and lets me know that it's helpful.
-   **Contributing**: Bug reports, feature suggestions, and code contributions are always welcome!
-   **Donate**: If you'd like to support me directly, you can [buy me a coffee](https://ko-fi.com/ilhamtaufiq) or [Saweria](https://saweria.co/ilhamtau)

Thank you for your support!

## License

This project is licensed under the [MIT License](LICENSE).
