FROM geographica/gdal2:2.3.0

RUN mkdir /code
WORKDIR /code

RUN apt-get update && apt-get install -y python3-pip && pip3 install --upgrade pip

# ttp://click.pocoo.org/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ADD requirements.txt /code/
RUN pip install -r requirements.txt
