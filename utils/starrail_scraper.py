# utils/starrail_scraper.py
import re

from .models import Code, Duration, Reward
from .scraper_base import ScraperBase


class StarrailScraper(ScraperBase):
    def __init__(self):
        super().__init__(game_name="Honkai Star Rail", game_color="magenta")
        self.url = "https://honkai-star-rail.fandom.com/wiki/Redemption_Code"

    def _extract_rewards(self, cell) -> list[Reward]:
        """Ekstrak daftar hadiah dari kolom tabel."""
        rewards = []
        items = cell.find_all("span", class_="item")

        for item in items:
            name_tag = item.find("span", class_="item-text")
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)

            img_tag = item.find("img")
            img_url = ""
            if img_tag:
                src = img_tag.get("data-src") or img_tag.get("src")
                if src:
                    img_url = src.split(".png")[0] + ".png"

            rewards.append(Reward(name=name, image=img_url))

        return rewards

    def _extract_duration(self, text: str) -> Duration:
        """
        Parsing teks durasi untuk menangkap: Discovered, Valid (until), dan Expired.
        """
        # Regex fleksibel untuk menangkap bagian-bagian tanggal
        # Menggunakan (?: ... ) untuk non-capturing group pembatas

        discovered_match = re.search(r"Discovered: (.*?)(?:$|Valid|Expired|Notes)", text)
        valid_match = re.search(r"Valid(?: until)?: (.*?)(?:$|Discovered|Expired|Notes)", text)
        expired_match = re.search(r"Expired: (.*?)(?:$|Discovered|Valid|Notes)", text)

        return Duration(
            discovered=discovered_match.group(1).strip() if discovered_match else None,
            valid=valid_match.group(1).strip() if valid_match else None,
            expired=expired_match.group(1).strip() if expired_match else None,
        )

    def scrape(self):
        self.log("🔍 Memulai scraping...")
        soup = self.get_soup(self.url)
        results = []

        if soup:
            content = soup.find("div", class_="mw-parser-output")
            if content:
                table = content.find("table", class_="wikitable")

                if table:
                    rows = table.find_all("tr")[1:]  # Lewati header
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) < 4:
                            continue

                        # 1. Handle Multiple Codes
                        code_tags = cols[0].find_all("code")
                        if not code_tags:
                            continue

                        # 2. Ambil data kolom lainnya
                        server = cols[1].get_text(strip=True)
                        rewards = self._extract_rewards(cols[2])

                        # Ambil teks mentah & parse objek duration
                        duration_raw_txt = cols[3].get_text(strip=True)
                        duration = self._extract_duration(duration_raw_txt)

                        # 3. Tentukan Status berdasarkan data duration yang sudah diparse
                        status = "active"

                        if duration.expired:
                            status = "expired"
                        elif duration.valid and "Unknown" in duration.valid:
                            status = "active"
                        # Fallback cek teks mentah untuk memastikan
                        elif "Expired" in duration_raw_txt or "expired" in duration_raw_txt.lower():
                            status = "expired"

                        # 4. Loop setiap kode
                        for code_tag in code_tags:
                            code_txt = code_tag.get_text(strip=True)
                            code_clean = re.sub(r"[^A-Z0-9]", "", code_txt.upper())

                            if not code_clean:
                                continue

                            results.append(
                                Code(
                                    code=code_clean,
                                    server=server,
                                    status=status,
                                    rewards=rewards,
                                    duration=duration,
                                )
                            )

            self.log(f"Total kode ditemukan: {len(results)}")
            self.save_results(results)
