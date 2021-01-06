from layman import settings


def test_default_srs_list():
    assert settings.LAYMAN_OUTPUT_SRS_LIST == [4326, 3857]
