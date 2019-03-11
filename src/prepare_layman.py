import pathlib
from layman_settings import *

def main():
    pathlib.Path(LAYMAN_DATA_DIR).mkdir(exist_ok=True, parents=True)

if __name__ == "__main__":
    main()