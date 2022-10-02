# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Setup
ENV APP_HOME /app
WORKDIR $APP_HOME

# Install poetry:
RUN pip install poetry

# Copy in the config files:
COPY pyproject.toml poetry.lock ./

# Install only dependencies:
RUN poetry config virtualenvs.in-project true && poetry install --no-dev

# Copy in everything else and install:
COPY . .

# Set application variables
ENV PROD_MODE 1

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
# CMD exec poetry run gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 0 --threads 8 app.main:app
ENV PORT 8000
EXPOSE $PORT
CMD exec poetry run uwsgi --http :$PORT --master --processes 1 --threads 8 -w app.main:app