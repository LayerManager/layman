import os
import shutil
import pathlib
from settings import LAYMAN_DATA_PATH, TESTING

def main():
    if TESTING:
        if os.path.exists(LAYMAN_DATA_PATH):
            shutil.rmtree(LAYMAN_DATA_PATH)
    pathlib.Path(LAYMAN_DATA_PATH).mkdir(exist_ok=True)

if __name__ == "__main__":
    main()