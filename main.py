# main.py
import concurrent.futures
import os
import shutil
import argparse

# Import the specific scraper classes
from utils.genshin_scraper import GenshinScraper
from utils.honkai_scraper import HonkaiScraper
from utils.starrail_scraper import StarrailScraper


def reset_folders():
    """Deletes and recreates game-specific data folders."""
    print("🔄 Resetting data folders...")
    for folder in ["genshin", "honkai", "starrail"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
    print("✅ Folders have been reset.")


def main(should_reset=False):
    """Initializes and runs all game scrapers."""
    if should_reset:
        reset_folders()

    scrapers = [
        GenshinScraper(),
        HonkaiScraper(),
        StarrailScraper(),
    ]

    # Run scrapers in parallel for efficiency
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
        executor.map(lambda s: s.run(), scrapers)

    print("\n✅ All scrapers have finished their tasks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape promotional codes for Hoyoverse games."
    )
    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="Reset all data folders before running.",
    )
    args = parser.parse_args()
    main(should_reset=args.reset)
