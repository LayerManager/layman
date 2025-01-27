import tools.client
from tools.oauth2_provider_mock import OAuth2ProviderMock


def main():
    username = 'test_migrate_2_user_1'
    print(f"Reserving username {username}")
    with OAuth2ProviderMock():
        client = tools.client.RestClient("http://localhost:8000")
        client.reserve_username(username, actor_name=username)


if __name__ == "__main__":
    main()
