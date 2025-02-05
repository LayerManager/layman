from layman import settings
from . import get_usernames
from .util import image_mosaic_granules_to_wms_time_key


def test_layman_gs_user_not_in_get_usernames():
    usernames = get_usernames()
    assert settings.LAYMAN_GS_USER not in usernames


IMAGE_MOSAIC_GRANULES_SAMPLE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "location": "S2A_MSIL2A_20220319T100731.2.tif",
                "ingestion": "2022-03-19T00:00:00.000Z",
                "elevation": None
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[543100, 5567910], [543100, 5572500], [553100, 5572500], [553100, 5567910], [543100, 5567910]]]]
            },
            "id": "s2a_msil2a_20220316t100031_0.1"
        },
        {
            "type": "Feature",
            "properties": {
                "location": "S2A_MSIL2A_20220319T100731.3.tif",
                "ingestion": "2022-03-19T00:00:00.000Z",
                "elevation": None
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[553100, 5567910], [553100, 5572500], [560930, 5572500], [560930, 5567910], [553100, 5567910]]]]
            },
            "id": "s2a_msil2a_20220316t100031_0.2"
        },
        {
            "type": "Feature",
            "properties": {
                "location": "S2A_MSIL2A_20220316T100031.2.tif",
                "ingestion": "2022-03-16T00:00:00.000Z",
                "elevation": None
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[543100, 5567910], [543100, 5573500], [552100, 5573500], [552100, 5567910], [543100, 5567910]]]]
            },
            "id": "s2a_msil2a_20220316t100031_0.4"
        }
    ]
}


def test_image_mosaic_granules_to_wms_time_key():
    assert image_mosaic_granules_to_wms_time_key(IMAGE_MOSAIC_GRANULES_SAMPLE) == {
        'units': 'ISO8601',
        'values': ['2022-03-16T00:00:00.000Z', '2022-03-19T00:00:00.000Z'],
        'default': '2022-03-19T00:00:00.000Z',
    }
