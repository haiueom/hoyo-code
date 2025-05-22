import json
import os
import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List, Optional


# === Data Classes ===
@dataclass
class Reward:
    name: str = ""
    image: str = ""


@dataclass
class Duration:
    discovered: Optional[str] = None
    valid: Optional[str] = None
    expired: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Code:
    code: str
    link: str
    server: str
    status: str
    rewards: List[Reward]
    duration: Duration


# === Util Functions ===
def extract_reward_info(cell) -> Reward:
    """Extract reward name and image from the cell."""
    name = cell.find("span", class_="item-text").text.strip()
    img_tag = cell.find("span", class_="item-image").find("img")

    image_url = img_tag.get("data-src") or img_tag.get("src") if img_tag else None
    if image_url:
        image_url = re.sub(r"\.(png|jpe?g|gif|bmp|svg|webp).*", r".\1", image_url)
        image_url += "/revision/latest"

    return Reward(name=name, image=image_url or "")


def extract_duration_info(cell) -> Duration:
    """Extract duration fields using regex."""
    text = cell.text.strip()
    if cell.find_all("b"):
        text += " " + " ".join(b.text for b in cell.find_all("b"))

    pattern = re.compile(
        r"Discovered: (\S+ \d+, \d+)"
        r"(?:.*?Valid(?: until)?: ((?:\([^)]+\))|(?:\S+ \S+ \d+(?:, \d+)?)|Unknown))?"
        r"(?:.*?Expired: (\S+ \d+, \d+))?"
        r"(?:.*?Notes: (.+))?"
    )
    match = pattern.match(text)
    if match:
        discovered, valid, expired, notes = (
            x.strip() if x else None for x in match.groups()
        )
        return Duration(discovered, valid, expired, notes)

    return Duration()


def determine_status(duration: Duration) -> str:
    """Determine if the code is active or expired."""
    return (
        "active"
        if duration.valid
        and "expired" not in (duration.valid.lower() if duration.valid else "")
        else "expired"
    )


def parse_row(row) -> List[Code]:
    """Parse a single row of the redemption table."""
    cols = row.find_all("td")
    if len(cols) < 4:
        return []

    codes = [code.text for code in cols[0].find_all("code")]
    link_tag = (
        cols[0].find_all("a")[1]
        if cols[0].find("sup") and len(cols[0].find_all("a")) > 1
        else cols[0].find("a")
    )
    link = link_tag.get("href") if link_tag else ""

    server = cols[1].text.strip()
    rewards = [
        extract_reward_info(cell) for cell in cols[2].find_all("span", class_="item")
    ]
    duration = extract_duration_info(cols[3])
    status = determine_status(duration)

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


# === File I/O ===
def save_json(file: str, data: List[Code]) -> None:
    with open(file, "w", encoding="utf-8") as f:
        json.dump([asdict(code) for code in data], f, indent=4, ensure_ascii=False)


def save_txt(file: str, data: List[Code]) -> None:
    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(code.code for code in data))


# === Scraping Logic ===
def scrape_codes() -> List[Code]:
    url = "https://honkai-star-rail.fandom.com/wiki/Redemption_Code"
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    rows = soup.select("table tbody tr")
    return [code for row in rows for code in parse_row(row)]


def send_discord_notification(code: Code):
    embed = {
        "title": f"Starrail: `{code.code}`",
        "color": 0x00FFFF,
        "description": f"```Server: {code.server}\nLink: {code.link}\n\n",
        "image": {"url": "https://i.ibb.co.com/Nng6s2rR/starrail.jpg"},
        "footer": {"text": "Hoyo Code"},
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
        response = requests.post(os.getenv("DC_WH"), json={"embeds": [embed]})
        response.raise_for_status()
        print(f"✅ [Starrail] Notifikasi dikirim untuk kode: {code.code}")
    except Exception as e:
        print(f"❌ [Starrail] Gagal kirim notifikasi: {e}")


# === Main Entry ===
def main():
    print("🔎 [Starrail] Mengecek kode terbaru...")
    all_codes = scrape_codes()
    active = [code for code in all_codes if code.status == "active"]
    expired = [code for code in all_codes if code.status == "expired"]

    old_codes = []
    if os.path.exists("starrail/all.json"):
        with open("starrail/all.json", "r", encoding="utf-8") as f:
            old_codes = json.load(f)
    old_active_codes = {c["code"] for c in old_codes}

    # Check for new active codes
    new_active_codes = [c for c in active if c.code not in old_active_codes]

    if new_active_codes:
        for code in new_active_codes:
            send_discord_notification(code)

    save_json("starrail/all.json", all_codes)
    save_json("starrail/active.json", active)
    save_json("starrail/expired.json", expired)
    save_txt("starrail/all.txt", all_codes)
    save_txt("starrail/active.txt", active)
    save_txt("starrail/expired.txt", expired)

    print(
        f"✅ [Starrail] Total: {len(all_codes)}, Aktif: {len(active)}, Expired: {len(expired)}"
    )
    if new_active_codes:
        print(
            f"📢 [Starrail] {len(new_active_codes)} kode baru ditemukan dan sudah dikirim ke Discord."
        )
    else:
        print("❎ [Starrail] Tidak ada kode baru.")


if __name__ == "__main__":
    main()
