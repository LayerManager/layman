FROM geographica/gdal2:2.4.0

RUN mkdir /code
WORKDIR /code

RUN apt-get update && \
    apt-get install -y unzip curl python3-pip && \
    pip3 install pipenv

# ttp://click.pocoo.org/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY Pipfile* /code/

# we need specific version of tornado because of celery/flower bug:
# https://github.com/mher/flower/issues/878
RUN pipenv install --system
