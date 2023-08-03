import os
import layman_settings as settings


ATTEMPT_INTERVAL = 2
MAX_ATTEMPTS = 60


def main():
    if os.getenv('LAYMAN_SKIP_REDIS_LOADING', 'false').lower() != 'true':
        print('Flushing Redis DB')
        settings.LAYMAN_REDIS.flushdb()
        print('Flushing LTC Redis DB')
        settings.LAYMAN_LTC_REDIS.flushdb()
    else:
        print('Not flushing Redis DB Redis DB')


if __name__ == "__main__":
    main()
