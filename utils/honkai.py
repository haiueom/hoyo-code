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
    image = reward_cell.find("img")
    if image:
        reward_image = image.get("data-src", image.get("src", None))
        if reward_image:
            pattern = re.compile(r"\.(png|jpg|jpeg|gif|bmp|svg|webp).*")
            reward_image = pattern.sub(r".\1", reward_image) + "/revision/latest"
    else:
        reward_image = ""

    reward_name = reward_cell.find("b").text.strip()

    return Reward(name=reward_name, image=reward_image)


def parse_row(row) -> Code:
    cols = row.find_all("td")
    codes = Code(
        code=cols[0].find("b").text.strip(),
        server="Global only, covering NA and EU. For any other region, such as SEA, CN, JP, or KR, these codes will not work",
        status="expired" if "Yes" in cols[4].text.strip() else "active",
        rewards=[
            extract_reward_info(cell)
            for cell in cols[3].find_all("div", class_="infobox-half")
        ],
        duration={"discovered": cols[1].text.strip(), "note": cols[2].text.strip()},
    )
    return codes


def write_json(file, data) -> None:
    with open(file, "w+") as f:
        json.dump(data, f, indent=4, default=lambda o: o.__dict__)


def write_txt(file: str, data: list[Code]) -> None:
    with open(file, "w+") as f:
        for i, entry in enumerate(data):
            f.write(entry.code)
            if i < len(data) - 1:
                f.write("\n")


def scrape_all() -> list[Code]:
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
    try:
        all = scrape_all()
        active = [code for code in all if code.status == "active"]
        expired = [code for code in all if code.status == "expired"]

        write_json("honkai/all.json", all)
        write_txt("honkai/all.txt", all)
        print(f"✅ Honkai: {len(all)} codes")

        write_json("honkai/active.json", active)
        write_txt("honkai/active.txt", active)
        print(f"✅ Honkai: {len(active)} active codes")

        write_json("honkai/expired.json", expired)
        write_txt("honkai/expired.txt", expired)
        print(f"✅ Honkai: {len(expired)} expired codes")
    except:
        print("❎ Honkai: Error retrieving data")


if __name__ == "__main__":
    main()
