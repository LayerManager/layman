# Changelog

## v1.2.1
2020-03-20
### Upgrade requirements
- Change [CSW_URL](doc/env-settings.md#CSW_URL) from `http://micka:80/csw` to `http://micka:80/micka/csw`

### Changes
- Fix URL prefix of Micka GUI in Layman v1.2.0, [#49](https://github.com/jirik/layman/issues/49) 

## v1.2.0
2020-03-18

### Upgrade requirements
- Upgrade Micka to [v2020.010](https://github.com/hsrs-cz/Micka/releases/tag/v2020.010).
- Add [CSW_PROXY_URL](doc/env-settings.md#CSW_PROXY_URL) to distinguish between internal CSW URL for Layman and public CSW URL for clients.
- Rename host [LAYMAN_TIMGEN_URL](doc/env-settings.md#LAYMAN_TIMGEN_URL) of from `hslayers` to `timgen`.

### Changes
- Publish metadata record of [map](doc/models.md#map) to Micka on [POST Maps](doc/rest.md#post-maps).
- Add `metatada` info to [GET Map](doc/rest.md#get-map) response.
- Extend `metatada` info with `identitier` attribute in case of both layer and map.
- Add documentation of [map metadata properties](doc/metadata.md)
- Use `metadataStandardName` and `metadataStandardVersion` in metadata templates
- Adjust metadata XML instead of using string formatting
- Rename metadata properties. All metadata-record-related properties have `md_` prefix. Dataset-related properties do not have any special prefix.

    |Old name|New name|
    |---|---|
    |`data_identifier`|`identifier`|
    |`data_organisation_name`|`organisation_name`|
    |`dataset_language`|`language`|
    |`date`|`publication_date`|
    |`date_stamp`|`md_date_stamp`|
    |`file_identifier`|`md_file_identifier`|
    |`organisation_name`|`md_organisation_name`|

- Add LaymanError 38 (Micka HTTP or connection error)
- Treat attribute names in SLD (aka 'launder'), [#45](https://github.com/jirik/layman/issues/45)
- Fix Micka's About URL in wait_for_deps
- Assert version of Micka on startup.
- Load data into redis on startup even in Flower.
- Better handle Micka's HTTP errors, [#43](https://github.com/jirik/layman/issues/43)
- Rename hslayers container to timgen (Thumbnail Image Generator)

## v1.1.8
2020-03-16
- Treat attribute names in SLD (aka 'launder'), [#45](https://github.com/jirik/layman/issues/45)
- Fix Micka's About URL in wait_for_deps

## v1.1.7
2020-03-09
- Assert version of Micka on startup.

## v1.1.6
2020-03-02
- Mute 500 error on CSW delete.

## v1.1.5
2020-02-28

Prior to 1.1.5, existing usernames, layers and maps **were not imported sometimes** on Layman's startup, that made it appear as they are missing. It should be fixed now by loading data into redis on startup even in Flower container.

## v1.1.4
2020-02-19
- Better handle Micka's HTTP errors, [#43](https://github.com/jirik/layman/issues/43)

## v1.1.3
2020-01-31
- Improve documentation of [enviroment variables](doc/env-settings.md)
- Show real info instead of just SUCCESS status in successfully finished tasks within GET Layer, GET Map, etc.
- Check freshness of links and image URLs in documentation within CI
- Add few words about Layman in [EN](doc/about.md) ans [CS](doc/cs/o-aplikaci.md)

## v1.1.2
2019-12-26
- Allow requesting layman from other docker containers (fix [#38](https://github.com/jirik/layman/issues/38))

## v1.1.1
2019-12-23
- Fix PENDING in state after celery task is removed from redis

## v1.1.0
2019-12-23
- Publish metadata record of [layer](doc/models.md#layer) to Micka on [POST Layers](doc/rest.md#post-layers). Connection to Micka is configurable using [CSW_*](doc/env-settings.md) environment variables.
- Delete metadata record of layer from Micka on [DELETE Layer](doc/rest.md#delete-layer).
- Add `metatada` info to [GET Layer](doc/rest.md#get-layer) response, including CSW URL and metadata record URL.
- [Documentation of metadata](doc/metadata.md)
- [LAYMAN_PROXY_SERVER_NAME](doc/env-settings.md#LAYMAN_PROXY_SERVER_NAME) environment variable
- Do not depend on specific version of chromium-browser and chromedriver
- Save write-lock to redis on POST, PATCH and DELETE of Layer and Map
- Enable to run Layman using multiple WSGI Flask processes by moving information about tasks from memory to redis
- Use Flask decorators
- Unify async task names, call task methods in the same way (src/layman/common/tasks.py#get_task_methods, src/layman/common/tasks.py#get_task_methods#tasks_util.get_chain_of_methods, src/layman/celery.py#set_publication_task_info)
