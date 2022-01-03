import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def get_session(*, retries=5):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=0.2,  # Used to compute time in seconds between attempts:
                             # backoff_factor * (2 ** attempt_idx - 1))
                             # if backoff_factor=0.2, it waits for [0.1, 0.2, 0.4, 0.8, ...]
        status_forcelist=(500,),
        method_whitelist=('HEAD', 'TRACE', 'GET', 'PUT', 'OPTIONS', 'DELETE', 'POST', 'PATCH')
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
