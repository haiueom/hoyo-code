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
class Codes:
    code: str = ""
    date: str = ""
    status: str = ""
    note: str = ""
    rewards: list[Reward] = None


def extract_reward_info(reward_cell) -> Reward:
    image = reward_cell.find("img")
    reward_image = image.get("data-src", image.get("src"))
    if reward_image:
        pattern = re.compile(r"\.(png|jpg|jpeg|gif|bmp|svg|webp).*")
        reward_image = pattern.sub(r".\1", reward_image) + "/revision/latest"

    reward_name = reward_cell.find("b").text.strip()

    return Reward(name=reward_name, image=reward_image)


def parse_row(row) -> Codes:
    cols = row.find_all("td")
    codes = Codes(
        code=cols[0].find("b").text.strip(),
        date=cols[1].text.strip(),
        status="Expired" if "Yes" in cols[4].text.strip() else "Valid",
        note=cols[2].text.strip(),
        rewards=[extract_reward_info(cell) for cell in cols[3].find_all("div", class_="infobox-half")],
    )
    return codes


def write_json(file, data) -> None:
    with open(file, "w+") as f:
        json.dump(data, f, indent=4, default=lambda o: o.__dict__)


def scrape_all() -> list[Codes]:
    URL = "https://honkaiimpact3.fandom.com/wiki/Exchange_Rewards"
    page = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find("div", class_="mw-parser-output").find_all("table")
    datas = []
    for table in tables:
        table_body = table.find("tbody")
        rows = table_body.find_all("tr")
        rows = rows[1:]
        for row in rows:
            data = parse_row(row)
            datas.append(data)
    return datas


def main() -> None:
    all = scrape_all()
    active = [code for code in all if code.status == "Valid"]
    expired = [code for code in all if code.status == "Expired"]
    write_json("honkai/all.json", all)
    write_json("honkai/active.json", active)
    write_json("honkai/expired.json", expired)
    return print("Honkai done!")

if __name__ == "__main__":
    main()
