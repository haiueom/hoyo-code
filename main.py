import concurrent.futures
import os

from utils.genshin import main as genshin
from utils.honkai import main as honkai
from utils.starrail import main as starrail


def check_dirs():
    if not os.path.exists("genshin"):
        os.makedirs("genshin")
    if not os.path.exists("honkai"):
        os.makedirs("honkai")
    if not os.path.exists("starrail"):
        os.makedirs("starrail")


def main():
    check_dirs()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(genshin),
            executor.submit(honkai),
            executor.submit(starrail),
        ]

        concurrent.futures.wait(futures)

    print("✅ Data updated")


if __name__ == "__main__":
    main()
