# utils/scraper_base.py
from time import sleep
from datetime import datetime, timedelta, timezone
import os
import json
import requests
from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import List, Set
from .models import Code


class ScraperBase(ABC):
    """Abstract base class for a Hoyoverse game code scraper."""

    def __init__(self, game_name: str, game_color: str, discord_image_url: str):
        self.game_name = game_name
        self.game_color = game_color
        self.game_folder = game_name.split()[0].lower()
        self.discord_image_url = discord_image_url
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        os.makedirs(self.game_folder, exist_ok=True)

    @abstractmethod
    def scrape(self) -> List[Code]:
        """Scrapes codes from the source. Must be implemented by subclasses."""
        raise NotImplementedError

    def _save_json(self, filename: str, data: List[Code]):
        """Saves a list of Code objects to a JSON file."""
        path = os.path.join(self.game_folder, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in data], f, indent=4, ensure_ascii=False)

    def _save_txt(self, filename: str, data: List[Code]):
        """Saves a list of code strings to a TXT file."""
        path = os.path.join(self.game_folder, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(c.code for c in data))

    def _get_old_active_codes(self) -> Set[str]:
        """Reads previously saved active codes to check against."""
        filepath = os.path.join(self.game_folder, "active.json")
        if not os.path.exists(filepath):
            return set()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                old_codes_data = json.load(f)
            return {c["code"] for c in old_codes_data}
        except (json.JSONDecodeError, FileNotFoundError):
            return set()

    def _send_discord_notification(self, code: Code):
        """Sends a notification to a Discord webhook for a new code."""
        if not self.discord_webhook_url:
            print(f"⚠ [{self.game_name}] Discord webhook not configured.")
            return

        rewards_str = (
            "\n".join([f"- {r.name}" for r in code.rewards]) if code.rewards else "N/A"
        )

        description_parts = [
            f"**Server:** {code.server}",
            f"**Link:** {code.link if code.link else 'N/A'}",
            f"\n**Rewards:**\n{rewards_str}\n",
        ]

        if code.duration.notes:
            description_parts.append(f"**Notes:** {code.duration.notes}")
        if code.duration.discovered:
            description_parts.append(f"**Discovered:** {code.duration.discovered}")
        if code.duration.valid:
            description_parts.append(f"**Valid Until:** {code.duration.valid}")

        embed = {
            "title": f"`{code.code}`",
            "description": "\n".join(description_parts),
            "color": self.game_color,
            "author": {"name": f"{self.game_name}"},
            "image": {"url": self.discord_image_url},
            "footer": {"text": "Hoyo Code"},
            "timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        }

        try:
            requests.post(
                self.discord_webhook_url, json={"embeds": [embed]}, timeout=10
            ).raise_for_status()
            print(f"✅ [{self.game_name}] Notification sent for code: {code.code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ [{self.game_name}] Failed to send Discord notification: {e}")

    def run(self):
        """Main execution logic for the scraper."""
        print(f"🔎 [{self.game_name}] Checking for new codes...")
        try:
            all_codes = self.scrape()
            active_codes = [c for c in all_codes if c.status == "active"]
            expired_codes = [c for c in all_codes if c.status == "expired"]

            old_active_codes_set = self._get_old_active_codes()
            new_active_codes = [
                c for c in active_codes if c.code not in old_active_codes_set
            ]

            if new_active_codes:
                for code in new_active_codes:
                    sleep(1)
                    self._send_discord_notification(code)

            # Save all files
            self._save_json("all.json", all_codes)
            self._save_json("active.json", active_codes)
            self._save_json("expired.json", expired_codes)
            self._save_txt("all.txt", all_codes)
            self._save_txt("active.txt", active_codes)
            self._save_txt("expired.txt", expired_codes)

            print(
                f"✅ [{self.game_name}] Total: {len(all_codes)}, Active: {len(active_codes)}, Expired: {len(expired_codes)}"
            )
            if new_active_codes:
                print(
                    f"📢 [{self.game_name}] {len(new_active_codes)} new code(s) found and sent to Discord."
                )
            else:
                print(f"❎ [{self.game_name}] No new codes found.")
        except Exception as e:
            print(f"❌ [{self.game_name}] An error occurred: {e}")
