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
    text = duration_text.text.strip()
    if duration_text.find_all("b"):
        text = text + " ".join([b.text for b in duration_text.find_all("b")])
    pattern = re.compile(
        r"Discovered: (\S+ \d+, \d+)(?:.*?Valid(?: until)?: ((?:\([^)]+\))|(?:\S+ \S+ \d+(?:, \d+)?)|Unknown))?(?:.*?Expired: (\S+ \d+, \d+))?(?:.*?Notes: (.+))?"
    )
    match = pattern.match(text)
    if match:
        groups = map(lambda x: x.strip() if x else None, match.groups())
        return Duration(*groups)
    return None


def extract_status_info(duration_info) -> str:
    if duration_info and duration_info.valid:
        return "active"
    else:
        return "expired"


def parse_row(row) -> list[Code]:
    cols = row.find_all("td")
    if len(cols) >= 2:
        codes = [code.text for code in cols[0].find_all("code")]
        if codes:
            return [
                Code(
                    code=code,
                    link=(
                        cols[0].find_all("a")[1].get("href")
                        if cols[0].find("sup")
                        else cols[0].find("a").get("href")
                    ),
                    server=cols[1].text.strip(),
                    rewards=[
                        extract_reward_info(cell)
                        for cell in cols[2].find_all("span", class_="item")
                    ],
                    duration=extract_duration_info(cols[3]),
                    status=extract_status_info(extract_duration_info(cols[3])),
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


def scrape_all() -> list[Code]:
    URL = "https://honkai-star-rail.fandom.com/wiki/Redemption_Code"
    page = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    table = soup.find("table")
    table_body = table.find("tbody")
    rows = table_body.find_all("tr")
    data = [info for row in rows for info in parse_row(row)]
    return data


def main() -> None:
    try:
        all_codes = scrape_all()
        active = [code for code in all_codes if code.status == "active"]
        expired = [code for code in all_codes if code.status == "expired"]

        write_json("starrail/all.json", all_codes)
        write_txt("starrail/all.txt", all_codes)
        print(f"✅ Starrail: {len(all_codes)} codes")

        write_json("starrail/active.json", active)
        write_txt("starrail/active.txt", active)
        print(f"✅ Starrail: {len(active)} active codes")

        write_json("starrail/expired.json", expired)
        write_txt("starrail/expired.txt", expired)
        print(f"✅ Starrail: {len(expired)} expired codes")
    except:
        print("❎ Starrail: Error retrieving data")


if __name__ == "__main__":
    main()
