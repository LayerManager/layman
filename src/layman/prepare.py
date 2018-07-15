import pathlib
from settings import *

def main():
    pathlib.Path(LAYMAN_DATA_PATH).mkdir(exist_ok=True)

if __name__ == "__main__":
    main()