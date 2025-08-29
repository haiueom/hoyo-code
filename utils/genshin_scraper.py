# utils/genshin_scraper.py
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from .scraper_base import ScraperBase
from .models import Reward, Duration, Code


class GenshinScraper(ScraperBase):
    def __init__(self):
        super().__init__(
            game_name="Genshin Impact",
            game_color=0x1E90FF,
            discord_image_url="https://i.ibb.co/LXYMB75y/genshin.jpg",
        )
        self.active_url = "https://genshin-impact.fandom.com/wiki/Promotional_Code"
        self.history_url = (
            "https://genshin-impact.fandom.com/wiki/Promotional_Code/History"
        )

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = requests.get(
                url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _extract_reward_info(self, cell) -> Reward:
        name = cell.find("span", class_="item-text").text.strip()
        image_el = cell.find("span", class_="item-image").find("img")
        image = image_el.get("data-src") or image_el.get("src") if image_el else None
        if image:
            image = (
                re.sub(r"\.(png|jpg|jpeg|gif|bmp|svg|webp).*", r".\1", image)
                + "/revision/latest"
            )
        return Reward(name=name, image=image or "")

    def _extract_duration_info(self, text: str) -> Duration:
        pattern = re.compile(
            r"Discovered: (\S+ \d+, \d+)"
            r"(?:.*?Valid(?: until)?: ((?:\([^)]+\))|(?:\S+ \S+ \d+(?:, \d+)?)))?"
            r"(?:.*?Expired: (\S+ \d+, \d+))?"
            r"(?:.*?Notes: (.+))?"
        )
        match = pattern.match(text)
        if match:
            groups = [g.strip() if g else None for g in match.groups()]
            return Duration(
                discovered=groups[0],
                valid=groups[1],
                expired=groups[2],
                notes=groups[3],
            )
        return Duration()

    def _parse_row(self, row, status: str) -> List[Code]:
        cols = row.find_all("td")
        if len(cols) < 4:
            return []

        code_tags = cols[0].find_all("code")
        if not code_tags:
            return []

        codes = [c.text.strip() for c in code_tags]
        link = cols[0].find("a").get("href", "") if cols[0].find("a") else ""
        server = cols[1].text.strip()
        rewards = [
            self._extract_reward_info(span)
            for span in cols[2].find_all("span", class_="item")
        ]
        duration = self._extract_duration_info(cols[3].text.strip())

        return [
            Code(
                code=c,
                link=link,
                server=server,
                status=status,
                rewards=rewards,
                duration=duration,
            )
            for c in codes
        ]

    def _scrape_page(self, url: str, status: str) -> List[Code]:
        soup = self._fetch_page(url)
        if not soup:
            return []

        table = soup.find("div", id="mw-content-text").find("table")
        if not table:
            return []

        rows = table.find("tbody").find_all("tr")
        return [code for row in rows for code in self._parse_row(row, status)]

    def scrape(self) -> List[Code]:
        active_codes = self._scrape_page(self.active_url, "active")
        expired_codes = self._scrape_page(self.history_url, "expired")
        return active_codes + expired_codes
