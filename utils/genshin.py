import json
import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class Reward:
    name: str = ""
    image: str = ""


@dataclass
class Duration:
    discovered: str = ""
    valid: str = ""
    expired: str = ""
    notes: str = ""


@dataclass
class Code:
    code: str = ""
    link: str = ""
    server: str = ""
    status: str = ""
    rewards: list[Reward] = list
    duration: Duration = dict


def extract_reward_info(reward_cell) -> Reward:
    reward_name = reward_cell.find("span", class_="item-text").text.strip()
    reward_image_element = reward_cell.find("span", class_="item-image").find("img")
    reward_image = (
        reward_image_element.get("data-src", reward_image_element.get("src", None))
        if reward_image_element
        else None
    )
    if reward_image:
        pattern = re.compile(r"\.(png|jpg|jpeg|gif|bmp|svg|webp).*")
        reward_image = pattern.sub(r".\1", reward_image) + "/revision/latest"
    return Reward(name=reward_name, image=reward_image)


def extract_duration_info(duration_text) -> Duration:
    pattern = re.compile(
        r"Discovered: (\S+ \d+, \d+)(?:.*?Valid(?: until)?: ((?:\([^)]+\))|(?:\S+ \S+ \d+(?:, \d+)?)))?(?:.*?Expired: (\S+ \d+, \d+))?(?:.*?Notes: (.+))?"
    )
    match = pattern.match(duration_text)
    if match:
        groups = map(lambda x: x.strip() if x else None, match.groups())
        return Duration(*groups)
    return None


def parse_row(row, status: str) -> list[Code]:
    cols = row.find_all("td")
    if len(cols) >= 2:
        codes = [code.text for code in cols[0].find_all("code")]
        if codes:
            return [
                Code(
                    code=code,
                    link=cols[0].find("a").get("href") if cols[0].find("a") else "",
                    server=cols[1].text.strip(),
                    rewards=[
                        extract_reward_info(cell)
                        for cell in cols[2].find_all("span", class_="item")
                    ],
                    duration=extract_duration_info(cols[3].text.strip()),
                    status=status,
                )
                for code in codes
            ]
    return []


def write_json(file: str, data: list[Code]) -> None:
    with open(file, "w+") as f:
        json.dump(data, f, indent=4, default=lambda o: o.__dict__)


def write_txt(file: str, data: list[Code]) -> None:
    with open(file, "w+") as f:
        for i, entry in enumerate(data):
            f.write(entry.code)
            if i < len(data) - 1:
                f.write("\n")


def scrape_active_codes() -> list[Code]:
    URL = "https://genshin-impact.fandom.com/wiki/Promotional_Code"
    page = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    table = soup.find("div", id="mw-content-text").find("table")
    table_body = table.find("tbody")
    rows = table_body.find_all("tr")
    data = [info for row in rows for info in parse_row(row, "active")]
    return data


def scrape_expired_codes() -> list[Code]:
    URL = "https://genshin-impact.fandom.com/wiki/Promotional_Code/History"
    page = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    table = soup.find("div", id="mw-content-text").find("table")
    table_body = table.find("tbody")
    rows = table_body.find_all("tr")
    data = [info for row in rows for info in parse_row(row, "expired")]
    return data


def main() -> None:
    try:
        active = scrape_active_codes()
        expired = scrape_expired_codes()

        write_json("genshin/all.json", active + expired)
        write_txt("genshin/all.txt", active + expired)
        print(f"✅ Genshin: {len(active + expired)} codes")

        write_json("genshin/active.json", active)
        write_txt("genshin/active.txt", active)
        print(f"✅ Genshin: {len(active)} active codes")

        write_json("genshin/expired.json", expired)
        write_txt("genshin/expired.txt", expired)
        print(f"✅ Genshin: {len(expired)} expired codes")
    except:
        print("❎ Genshin: Error retrieving data")


if __name__ == "__main__":
    main()
