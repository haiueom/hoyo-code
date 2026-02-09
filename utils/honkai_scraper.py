# utils/honkai_scraper.py
import re

from .models import Code, Duration, Reward
from .scraper_base import ScraperBase


class HonkaiScraper(ScraperBase):
    def __init__(self):
        super().__init__(game_name="Honkai Impact 3rd", game_color="cyan")
        self.url = "https://honkaiimpact3.fandom.com/wiki/Exchange_Rewards"

    def _extract_rewards(self, text: str) -> list[Reward]:
        """Ekstrak hadiah dari teks sederhana."""
        rewards_list = []
        items = re.split(r",|&|\+", text)

        for item in items:
            clean_name = item.strip()
            if clean_name:
                rewards_list.append(Reward(name=clean_name, image=""))

        return rewards_list

    def scrape(self):
        self.log("🔍 Memulai scraping...")
        soup = self.get_soup(self.url)
        results = []

        if soup:
            content = soup.find("div", class_="mw-parser-output")
            if not content:
                return

            tables = content.find_all("table", class_="wikitable")
            self.log(f"Ditemukan {len(tables)} tabel data.")

            for i, table in enumerate(tables):
                rows = table.find_all("tr")

                for row_idx, row in enumerate(rows):
                    # Lewati Header
                    if row_idx == 0:
                        continue

                    cols = row.find_all("td")

                    code_clean = ""
                    server_txt = ""
                    rewards = []
                    duration_txt = ""
                    status = "active"

                    # === LOGIKA TABEL 1 (ACTIVE CODES) ===
                    if i == 0:
                        # Biasanya struktur: [Code] [Rewards] [Expired/Duration]
                        # Minimal 3 kolom
                        if len(cols) < 5:
                            continue

                        # 1. Code
                        code_el = cols[1].find("code")
                        code_txt = (
                            code_el.get_text(strip=True)
                            if code_el
                            else cols[1].get_text(strip=True)
                        )
                        code_clean = re.sub(r"[^A-Z0-9]", "", code_txt.upper())

                        # 2. Date/Duration
                        duration_txt = cols[2].get_text(strip=True)

                        # 3. Occasion (Server Info)
                        server_txt = cols[3].get_text(strip=True)

                        # 4. Rewards
                        reward_txt = cols[4].get_text(strip=True)
                        rewards = self._extract_rewards(reward_txt)

                        # History pasti expired
                        status = "expired"

                    # === LOGIKA TABEL LAINNYA (HISTORY) ===
                    else:
                        # Struktur: [Code] [Date] [Occasion] [Rewards]
                        # Minimal 4 kolom
                        if len(cols) < 4:
                            continue

                        # 1. Code
                        code_el = cols[0].find("code")
                        code_txt = (
                            code_el.get_text(strip=True)
                            if code_el
                            else cols[0].get_text(strip=True)
                        )
                        code_clean = re.sub(r"[^A-Z0-9]", "", code_txt.upper())

                        # 2. Date/Duration
                        duration_txt = cols[1].get_text(strip=True)

                        # 3. Occasion (Server Info)
                        server_txt = cols[2].get_text(strip=True)

                        # 4. Rewards
                        reward_txt = cols[3].get_text(strip=True)
                        rewards = self._extract_rewards(reward_txt)

                        # History pasti expired
                        status = "expired"

                    if not code_clean:
                        continue

                    results.append(
                        Code(
                            code=code_clean,
                            server=server_txt,
                            status=status,
                            rewards=rewards,
                            duration=Duration(valid=duration_txt, notes=server_txt),
                        )
                    )

            self.log(f"Total kode ditemukan: {len(results)}")
            self.save_results(results)
