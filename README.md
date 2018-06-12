# gspld
Uploading files to GeoServer

## Dev installation
```bash
git clone https://github.com/jirik/gspld.git
cd gspld

# prepare geoserver data directory
GS_VERSION=2.13.0 make download-gs-datadir
sudo GS_VERSION=2.13.0 make reset-gs-datadir

# start geoserver & DB & docker
docker-compose up

# visit http://localhost:8000/
```

