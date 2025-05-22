import os
import re
import json
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List, Optional

# ===== Data Structure =====


@dataclass
class Reward:
    name: str
    image: str


@dataclass
class Duration:
    discovered: Optional[str]
    valid: Optional[str]
    expired: Optional[str]
    notes: Optional[str]


@dataclass
class Code:
    code: str
    link: str
    server: str
    status: str  # 'active' or 'expired'
    rewards: List[Reward]
    duration: Duration


# ===== Utility Functions =====


def extract_reward_info(cell) -> Reward:
    name = cell.find("span", class_="item-text").text.strip()
    image_el = cell.find("span", class_="item-image").find("img")
    image = image_el.get("data-src") or image_el.get("src") if image_el else None
    if image:
        image = (
            re.sub(r"\.(png|jpg|jpeg|gif|bmp|svg|webp).*", r".\1", image)
            + "/revision/latest"
        )
    return Reward(name=name, image=image)


def extract_duration_info(text: str) -> Duration:
    pattern = re.compile(
        r"Discovered: (\S+ \d+, \d+)"
        r"(?:.*?Valid(?: until)?: ((?:\([^)]+\))|(?:\S+ \S+ \d+(?:, \d+)?)))?"
        r"(?:.*?Expired: (\S+ \d+, \d+))?"
        r"(?:.*?Notes: (.+))?"
    )
    match = pattern.match(text)
    if match:
        groups = [g.strip() if g else None for g in match.groups()]
        return Duration(*groups)
    return Duration(None, None, None, None)


def parse_row(row, status: str) -> List[Code]:
    cols = row.find_all("td")
    if len(cols) < 2:
        return []
    codes = [c.text.strip() for c in cols[0].find_all("code")]
    if not codes:
        return []
    rewards = [
        extract_reward_info(span) for span in cols[2].find_all("span", class_="item")
    ]
    duration = extract_duration_info(cols[3].text.strip())
    link = cols[0].find("a").get("href", "") if cols[0].find("a") else ""
    server = cols[1].text.strip()
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


# ===== Scraper Functions =====


def scrape_codes(url: str, status: str) -> List[Code]:
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    table = soup.find("div", id="mw-content-text").find("table")
    rows = table.find("tbody").find_all("tr")
    return [code for row in rows for code in parse_row(row, status)]


def get_all_codes() -> List[Code]:
    active = scrape_codes(
        "https://genshin-impact.fandom.com/wiki/Promotional_Code", "active"
    )
    expired = scrape_codes(
        "https://genshin-impact.fandom.com/wiki/Promotional_Code/History", "expired"
    )
    return active + expired


# ===== Save Functions =====


def save_json(path: str, data: List[Code]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in data], f, indent=4)


def save_txt(path: str, data: List[Code]):
    with open(path, "w", encoding="utf-8") as f:
        for i, code in enumerate(data):
            f.write(code.code)
            if i < len(data) - 1:
                f.write("\n")


# ===== Discord Notification =====


def send_discord_notification(code: Code):
    embed = {
        "title": f"Genshin: `{code.code}`",
        "color": 0x00FFFF,
        "description": f"```Server: {code.server}\nLink: {code.link}\n\n",
        "footer": {"text": "Hoyo Code"},
        "image": {
            "url": "https://i.ibb.co.com/LXYMB75y/genshin.jpg",
        },
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
        response = requests.post(
            os.getenv("DC_WH"),
            json={"embeds": [embed]},
        )
        response.raise_for_status()
        print(f"✅ [Genshin] Notifikasi dikirim untuk kode: {code.code}")
    except Exception as e:
        print(f"❌ [Genshin] Gagal kirim notifikasi: {e}")


# ===== Main Logic =====


def main():
    print("🔎 [Genshin] Mengecek kode terbaru...")
    all_codes = get_all_codes()
    active_codes = [c for c in all_codes if c.status == "active"]
    expired_codes = [c for c in all_codes if c.status == "expired"]

    # Buat folder jika belum ada
    os.makedirs("genshin", exist_ok=True)

    # Cek kode baru hanya dari kode aktif
    old_codes = []
    if os.path.exists("genshin/active.json"):
        with open("genshin/active.json", "r", encoding="utf-8") as f:
            old_codes = json.load(f)
    old_active_codes = {c["code"] for c in old_codes}

    # Filter hanya kode aktif yang belum ada sebelumnya
    new_active_codes = [c for c in active_codes if c.code not in old_active_codes]

    # Kirim notifikasi untuk kode aktif baru
    for code in new_active_codes:
        send_discord_notification(code)

    # Simpan data terbaru
    save_json("genshin/all.json", all_codes)
    save_json("genshin/active.json", active_codes)
    save_json("genshin/expired.json", expired_codes)
    save_txt("genshin/all.txt", all_codes)
    save_txt("genshin/active.txt", active_codes)
    save_txt("genshin/expired.txt", expired_codes)

    print(
        f"✅ [Genshin] Total: {len(all_codes)}, Aktif: {len(active_codes)}, Expired: {len(expired_codes)}"
    )
    if new_active_codes:
        print(
            f"📢 [Genshin] {len(new_active_codes)} kode baru ditemukan dan sudah dikirim ke Discord."
        )
    else:
        print("❎ [Genshin] Tidak ada kode baru.")


if __name__ == "__main__":
    main()
