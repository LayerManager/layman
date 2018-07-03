import pathlib
from settings import LAYMAN_DATA_PATH

def main():
    pathlib.Path(LAYMAN_DATA_PATH).mkdir(exist_ok=True)

if __name__ == "__main__":
    main()