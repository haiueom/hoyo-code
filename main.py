import concurrent.futures
import os
import shutil
import argparse

from utils.genshin import main as genshin
from utils.honkai import main as honkai
from utils.starrail import main as starrail


def check_dirs():
    for folder in ["genshin", "honkai", "starrail"]:
        os.makedirs(folder, exist_ok=True)


def reset_folders():
    for folder in ["genshin", "honkai", "starrail"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    check_dirs()
    print("🔄 Folders have been reset.")


def main(reset=False):
    if reset:
        reset_folders()
    else:
        check_dirs()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(genshin),
            executor.submit(honkai),
            executor.submit(starrail),
        ]

        concurrent.futures.wait(futures)

    print("✅ [Main] Data updated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check and update data folders.")
    parser.add_argument("-r", "--reset", action="store_true", help="Reset all data folders before running.")

    args = parser.parse_args()
    main(reset=args.reset)
