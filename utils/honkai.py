import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List, Optional


DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


@dataclass
class Reward:
    name: str
    image: str


@dataclass
class Duration:
    discovered: str
    note: str


@dataclass
class Code:
    code: str
    link: Optional[str]
    server: str
    status: str
    rewards: List[Reward]
    duration: Duration


def extract_reward_info(cell) -> Reward:
    image_tag = cell.find("img")
    name = cell.find("b").text.strip() if cell.find("b") else ""

    if image_tag:
        reward_image = image_tag.get("data-src") or image_tag.get("src", "")
        pattern = re.compile(r"\.(png|jpg|jpeg|gif|bmp|svg|webp).*")
        reward_image = pattern.sub(r".\1", reward_image) + "/revision/latest"
    else:
        reward_image = ""

    return Reward(name=name, image=reward_image)


def parse_row(row) -> Optional[Code]:
    cols = row.find_all("td")
    if len(cols) < 5:
        return None

    code = cols[0].find("b").text.strip()
    discovered = cols[1].text.strip()
    note = cols[2].text.strip()
    status = "expired" if "Yes" in cols[4].text else "active"

    rewards = [
        extract_reward_info(div)
        for div in cols[3].find_all("div", class_="infobox-half")
    ]

    return Code(
        code=code,
        link=None,
        server="Global only (NA/EU)",
        status=status,
        rewards=rewards,
        duration=Duration(discovered=discovered, note=note),
    )


def scrape_all() -> List[Code]:
    URL = "https://honkaiimpact3.fandom.com/wiki/Exchange_Rewards"
    res = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.content, "html.parser")

    all_codes = []
    tables = soup.find("div", class_="mw-parser-output").find_all("table")

    for table in tables:
        rows = table.find_all("tr")[1:]  # skip header
        for row in rows:
            code = parse_row(row)
            if code:
                all_codes.append(code)

    return all_codes


def write_json(filepath: str, data: List[Code]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump([asdict(code) for code in data], f, indent=4, ensure_ascii=False)


def write_txt(filepath: str, data: List[Code]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(code.code for code in data))


def read_existing_codes(filepath: str) -> List[str]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]


def send_discord_notification(code: Code):
    embed = {
        "title": f"🎁 Genshin: `{code.code}`",
        "color": 0x00FFFF,
        "description": f"```Server: {code.server}\nLink: {code.link}\n\n",
        "footer": {"text": "Hoyo Code"},
        "image": {"url": "https://i.ibb.co.com/mryQSWvT/honkai.jpg"},
    }

    # Tambahkan reward jika ada
    if code.rewards:
        reward_list = "\n".join([f"- {r.name}" for r in code.rewards])
        embed["description"] += f"🎉 Rewards:\n{reward_list}\n\n"

    if code.duration.notes:
        embed["description"] += f"Notes: {code.duration.notes}\n```"

    if code.duration.discovered:
        embed["description"] += f"Discovered: {code.duration.discovered}\n"

    if code.duration.valid:
        embed["description"] += f"Valid Until: {code.duration.valid}\n"

    if code.duration.expired:
        embed["description"] += f"Expired: {code.duration.expired}\n"

    embed["description"] += "```"

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
        response.raise_for_status()
        print(f"✅ [Genshin] Notifikasi dikirim untuk kode: {code.code}")
    except Exception as e:
        print(f"❌ [Genshin] Gagal kirim notifikasi: {e}")


def main():
    all_codes = scrape_all()
    active_codes = [c for c in all_codes if c.status == "active"]
    expired_codes = [c for c in all_codes if c.status == "expired"]

    os.makedirs("honkai", exist_ok=True)

    write_json("honkai/all.json", all_codes)
    write_txt("honkai/all.txt", all_codes)

    write_json("honkai/active.json", active_codes)
    write_txt("honkai/active.txt", active_codes)

    write_json("honkai/expired.json", expired_codes)
    write_txt("honkai/expired.txt", expired_codes)

    # Notify only new active codes
    old_active = read_existing_codes("honkai/active.txt")
    new_codes = [code for code in active_codes if code.code not in old_active]

    for code in new_codes:
        send_discord_notification(code)

    print(
        f"✅ Honkai: {len(all_codes)} total, {len(active_codes)} active, {len(expired_codes)} expired"
    )
    if new_codes:
        print(f"📢 Sent {len(new_codes)} new active codes to Discord")


if __name__ == "__main__":
    main()
