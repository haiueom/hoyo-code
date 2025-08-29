# utils/starrail_scraper.py
import re
import requests
from bs4 import BeautifulSoup, Tag
from typing import List, Optional
from .scraper_base import ScraperBase
from .models import Reward, Duration, Code


class StarrailScraper(ScraperBase):
    """Scrapes redemption codes for Honkai: Star Rail."""

    def __init__(self):
        super().__init__(
            game_name="Honkai Starrail",
            game_color=0x8A2BE2,
            discord_image_url="https://i.ibb.co.com/Nng6s2rR/starrail.jpg",
        )
        self.url = "https://honkai-star-rail.fandom.com/wiki/Redemption_Code"

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
        name = cell.find("span", class_="item-text").text.strip()
        img_tag = cell.find("span", class_="item-image").find("img")

        image_url = ""
        if img_tag:
            raw_url = img_tag.get("data-src") or img_tag.get("src")
            if raw_url:
                image_url = (
                    re.sub(r"\.(png|jpe?g|gif|bmp|svg|webp).*", r".\1", raw_url)
                    + "/revision/latest"
                )

        return Reward(name=name, image=image_url)

    def _extract_duration_info(self, cell: Tag) -> Duration:
        """Extracts duration fields using regex for better accuracy."""
        text_content = cell.get_text(separator=" ", strip=True)

        pattern = re.compile(
            r"Discovered: (\S+ \d+, \d+)"
            r"(?:.*?Valid(?: until)?: ((?:\([^)]+\))|(?:\S+ \S+ \d+(?:, \d+)?)|Unknown))?"
            r"(?:.*?Expired: (\S+ \d+, \d+))?"
            r"(?:.*?Notes: (.+))?",
            re.DOTALL,
        )
        match = pattern.search(text_content)

        if match:
            discovered, valid, expired, notes = (
                x.strip() if x else None for x in match.groups()
            )
            return Duration(discovered, valid, expired, notes)

        return Duration()

    def _determine_status(self, duration: Duration) -> str:
        """Determines if the code is active or expired based on duration info."""
        if duration.valid and "expired" not in duration.valid.lower():
            return "active"
        return "expired"

    def _parse_row(self, row: Tag) -> List[Code]:
        """Parses a single table row to extract one or more codes."""
        cols = row.find_all("td")
        if len(cols) < 4:
            return []

        codes = [code.text for code in cols[0].find_all("code")]

        # Determine the correct link, handling multiple <a> tags
        link_tags = cols[0].find_all("a")
        link = ""
        if len(link_tags) > 1 and cols[0].find("sup"):
            link = link_tags[1].get("href", "")
        elif link_tags:
            link = link_tags[0].get("href", "")

        server = cols[1].text.strip()
        rewards = [
            self._extract_reward_info(cell)
            for cell in cols[2].find_all("span", class_="item")
        ]
        duration = self._extract_duration_info(cols[3])
        status = self._determine_status(duration)

        return [
            Code(
                code=code,
                link=link,
                server=server,
                rewards=rewards,
                duration=duration,
                status=status,
            )
            for code in codes
        ]

    def scrape(self) -> List[Code]:
        """Scrapes all codes from the main redemption code table."""
        soup = self._fetch_page()
        if not soup:
            return []

        table = soup.select_one("table.wikitable")
        if not table:
            return []

        rows = table.select("tbody tr")
        return [code for row in rows for code in self._parse_row(row)]
