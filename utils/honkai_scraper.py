# utils/honkai_scraper.py
import re
import requests
from bs4 import BeautifulSoup, Tag
from typing import List, Optional
from .scraper_base import ScraperBase
from .models import Reward, Duration, Code


class HonkaiScraper(ScraperBase):
    """Scrapes redemption codes for Honkai Impact 3rd."""

    def __init__(self):
        super().__init__(
            game_name="Honkai", discord_image_url="https://i.ibb.co/mryQSWvT/honkai.jpg"
        )
        self.url = "https://honkaiimpact3.fandom.com/wiki/Exchange_Rewards"

    def _fetch_page(self) -> Optional[BeautifulSoup]:
        """Fetches and parses the content of the wiki page."""
        try:
            response = requests.get(
                self.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            print(f"Error fetching {self.url}: {e}")
            return None

    def _extract_reward_info(self, cell: Tag) -> Reward:
        """Extracts reward information from a table cell."""
        name_tag = cell.find("b")
        name = name_tag.text.strip() if name_tag else ""

        image_tag = cell.find("img")
        image_url = ""
        if image_tag:
            raw_image_url = image_tag.get("data-src") or image_tag.get("src", "")
            # Clean up URL to get the base image and add revision for highest quality
            pattern = re.compile(r"\.(png|jpg|jpeg|gif|bmp|svg|webp).*")
            image_url = pattern.sub(r".\1", raw_image_url) + "/revision/latest"

        return Reward(name=name, image=image_url)

    def _parse_row(self, row: Tag) -> Optional[Code]:
        """Parses a table row to extract code information."""
        cols = row.find_all("td")
        if len(cols) < 5:
            return None

        code_text = cols[0].find("b").text.strip()
        discovered_date = cols[1].text.strip()
        notes = cols[2].text.strip()

        # Determine status based on the "Expired" column
        status = "expired" if "Yes" in cols[4].text else "active"

        rewards = [
            self._extract_reward_info(div)
            for div in cols[3].find_all("div", class_="infobox-half")
        ]

        return Code(
            code=code_text,
            link=None,  # Not available on this wiki page
            server="Global only (NA/EU)",
            status=status,
            rewards=rewards,
            duration=Duration(discovered=discovered_date, notes=notes),
        )

    def scrape(self) -> List[Code]:
        """Scrapes all code tables from the page."""
        soup = self._fetch_page()
        if not soup:
            return []

        all_codes: List[Code] = []
        content_area = soup.find("div", class_="mw-parser-output")
        if not content_area:
            return []

        tables = content_area.find_all("table")
        for table in tables:
            rows = table.find_all("tr")[1:]  # Skip header row
            for row in rows:
                code_obj = self._parse_row(row)
                if code_obj:
                    all_codes.append(code_obj)

        return all_codes
