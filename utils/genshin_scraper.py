# utils/genshin_scraper.py
import re

from .models import Code, Duration, Reward
from .scraper_base import ScraperBase


class GenshinScraper(ScraperBase):
    def __init__(self):
        super().__init__(game_name="Genshin Impact", game_color="blue")
        self.active_url = "https://genshin-impact.fandom.com/wiki/Promotional_Code"
        self.history_url = "https://genshin-impact.fandom.com/wiki/Promotional_Code/History"

    def _extract_reward(self, cell) -> list[Reward]:
        rewards = []
        items = cell.find_all("span", class_="item")
        for item in items:
            name_tag = item.find("span", class_="item-text")
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            # Logika gambar sederhana
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
        Parsing teks durasi untuk menangkap 4 kemungkinan:
        Discovered, Valid until, Expired, dan Note.
        """
        # Regex untuk menangkap masing-masing bagian
        # Menggunakan (?: ... ) untuk grup non-capturing pada delimiter

        discovered_match = re.search(r"Discovered: (.*?)(?:$|Valid|Expired|Note)", text)
        valid_match = re.search(r"Valid(?: until)?: (.*?)(?:$|Discovered|Expired|Note)", text)
        expired_match = re.search(r"Expired: (.*?)(?:$|Discovered|Valid|Note)", text)
        notes_match = re.search(r"Note(?:s)?: (.*?)(?:$|Discovered|Valid|Expired)", text)

        return Duration(
            discovered=discovered_match.group(1).strip() if discovered_match else None,
            valid=valid_match.group(1).strip() if valid_match else None,
            expired=expired_match.group(1).strip() if expired_match else None,
            notes=notes_match.group(1).strip() if notes_match else None,
        )

    def _parse_table(self, soup, status: str) -> list[Code]:
        codes = []
        if not soup:
            return codes

        # Cari div konten utama lalu tabel
        content = soup.find("div", class_="mw-parser-output")
        if not content:
            return codes

        table = content.find("table", class_="wikitable")
        if not table:
            return codes

        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            # Kolom 0: Kode (Ambil SEMUA tag code dalam satu sel)
            code_tags = cols[0].find_all("code")
            if not code_tags:
                continue

            # Ambil data umum baris ini
            server = cols[1].get_text(strip=True)
            rewards = self._extract_reward(cols[2])

            # Ambil teks durasi dengan separator spasi agar regex aman
            duration_txt = cols[3].get_text(separator=" ", strip=True)
            duration = self._extract_duration(duration_txt)

            # Loop untuk setiap kode yang ditemukan di kolom tersebut
            for code_tag in code_tags:
                code_txt = code_tag.get_text(strip=True)

                # Bersihkan kode
                code_clean = re.sub(r"[^A-Z0-9]", "", code_txt.upper())

                if not code_clean:
                    continue

                codes.append(
                    Code(
                        code=code_clean,
                        server=server,
                        status=status,
                        rewards=rewards,
                        duration=duration,
                    )
                )

        return codes

    def scrape(self):
        all_results = []

        self.log("🔍 Memulai scraping kode AKTIF...")
        soup_active = self.get_soup(self.active_url)
        if soup_active:
            codes = self._parse_table(soup_active, "active")
            self.log(f"Ditemukan {len(codes)} kode aktif.")
            all_results.extend(codes)

        self.log("🔍 Memulai scraping kode HISTORY (Expired)...")
        soup_expired = self.get_soup(self.history_url)
        if soup_expired:
            codes = self._parse_table(soup_expired, "expired")
            self.log(f"Ditemukan {len(codes)} kode kadaluarsa.")
            all_results.extend(codes)

        self.save_results(all_results)
