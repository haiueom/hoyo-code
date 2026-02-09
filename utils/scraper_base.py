# utils/scraper_base.py
import json
import os
import time
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup
from rich.console import Console

from .models import Code

# Inisialisasi Rich Console
console = Console()


class ScraperBase(ABC):
    def __init__(self, game_name: str, game_color: str):
        self.game_name = game_name
        self.game_color = game_color
        self.game_folder = game_name.split()[0].lower()
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

        # Buat folder jika belum ada
        os.makedirs(self.game_folder, exist_ok=True)

    def log(self, message: str, style: str = "white"):
        """Helper untuk logging dengan warna spesifik game."""
        console.print(
            f"[{self.game_color}][{self.game_name}][/{self.game_color}] {message}", style=style
        )

    def get_soup(self, url: str) -> BeautifulSoup | None:
        """
        Alur: Request (requests.get) -> Tunggu -> Parse
        """
        self.log(f"Mengambil data dari: [dim]{url}[/dim]")

        try:
            # Request POLOS tanpa headers custom
            response = requests.get(url, timeout=20)

            if response.status_code == 200:
                self.log("✅ Koneksi berhasil (200 OK). Menunggu halaman termuat...", style="green")

                # 1. Tunggu sejenak agar halaman 'settle' dan terlihat natural
                time.sleep(3)

                # 2. Parse dengan BeautifulSoup
                soup = BeautifulSoup(response.content, "html.parser")
                return soup

            elif response.status_code == 403:
                self.log("❌ Akses Ditolak (403 Forbidden).", style="bold red")
            else:
                self.log(f"⚠️ Gagal memuat halaman. Status: {response.status_code}", style="yellow")

        except Exception as e:
            self.log(f"❌ Error koneksi: {e}", style="bold red")

        return None

    def _send_discord_notification(self, code: Code):
        """Mengirim notifikasi ke Discord (Opsional)."""
        if not self.discord_webhook_url:
            return

        # Konversi warna string ke int (jika perlu)
        color_int = 0
        if self.game_color == "blue":
            color_int = 0x1E90FF  # Genshin
        elif self.game_color == "magenta":
            color_int = 0x8A2BE2  # Starrail
        elif self.game_color == "cyan":
            color_int = 0x00BFFF  # Honkai

        embed = {
            "title": f"`{code.code}`",
            "description": f"**Server:** {code.server}\n**Rewards:**\n"
            + ("\n".join([f"- {r.name}" for r in code.rewards]) if code.rewards else "N/A"),
            "color": color_int,
            "footer": {"text": "Hoyo Code Scraper"},
        }

        try:
            requests.post(self.discord_webhook_url, json={"embeds": [embed]}, timeout=10)
        except Exception:
            pass

    def save_results(self, codes: list[Code]):
        """Menyimpan data ke JSON dan TXT."""
        if not codes:
            self.log("Tidak ada kode untuk disimpan.", style="dim yellow")
            return

        # Pisahkan Active dan Expired
        active_codes = [c for c in codes if c.status == "active"]
        expired_codes = [c for c in codes if c.status == "expired"]

        data_map = {"all": codes, "active": active_codes, "expired": expired_codes}

        self.log(
            f"Menyimpan data... (Active: {len(active_codes)} | Expired: {len(expired_codes)})",
            style="cyan",
        )

        for key, data_list in data_map.items():
            # Simpan JSON
            json_path = os.path.join(self.game_folder, f"{key}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([c.model_dump() for c in data_list], f, indent=4, ensure_ascii=False)

            # Simpan TXT
            txt_path = os.path.join(self.game_folder, f"{key}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(c.code for c in data_list))

        self.log("✅ Data berhasil disimpan ke folder.", style="bold green")

    @abstractmethod
    def scrape(self):
        """Implementasi spesifik tiap game."""
        pass
