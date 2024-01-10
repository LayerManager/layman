FROM osgeo/gdal:ubuntu-small-3.3.0

ENV PYTHONUNBUFFERED 1

# Set the Django settings to use.
ENV DJANGO_ENV "dev"
ENV DJANGO_SETTINGS_MODULE "laymanportal.settings.dev"

RUN apt update && apt install -y python3-pip

# Install a WSGI server into the container image.
RUN pip install waitress

# Code will end up living in /app/
WORKDIR /app/

# Copy and install the project requirements.
COPY ./laymanportal/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy the entire project code.
COPY laymanportal /app/

# Prepare the app: migrations (not needed as db.sqlite3a was generated after migrations)
# RUN python manage.py migrate

# Prepare the app: collect static files
RUN python manage.py collectstatic --noinput

# Create a "coderedcms" user account to run the app.
RUN useradd coderedcms
RUN chown -R coderedcms /app/
USER coderedcms
