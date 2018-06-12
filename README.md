# gspld
Uploading files to GeoServer

## Installation
```bash
git clone https://github.com/jirik/gspld.git
cd gspld
GS_VERSION=2.13.0 make download-gs-datadir
sudo GS_VERSION=2.13.0 make reset-gs-datadir
docker-compose up
```

