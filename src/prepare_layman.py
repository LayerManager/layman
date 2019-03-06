import pathlib
from layman.settings import *

def main():
    pathlib.Path(LAYMAN_DATA_DIR).mkdir(exist_ok=True)

if __name__ == "__main__":
    main()