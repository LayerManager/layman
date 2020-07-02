import traceback

import importlib
import os
import sys
import time


settings = importlib.import_module(os.environ['LAYMAN_SETTINGS_MODULE'])

ATTEMPT_INTERVAL = 2
MAX_ATTEMPTS = 60


def main():

    if os.getenv('LAYMAN_SKIP_REDIS_LOADING', 'false').lower() != 'true':
        print('Flushing Redis DB')
        settings.LAYMAN_REDIS.flushdb()
    else:
        print('Not flushing Redis DB Redis DB')


if __name__ == "__main__":
    main()
