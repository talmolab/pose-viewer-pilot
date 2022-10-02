# pose-viewer-pilot

- [Cloud Run Project](https://console.cloud.google.com/run/detail/us-central1/pose-viewer-pilot/metrics?organizationId=284540140746&project=pose-viewer-pilot)

## Setup

### Setup with poetry

If you don't have `pipx` and `poetry` installed:

```
pip install pipx
```

```
pipx ensurepath
```

```
pipx install poetry
```

Then you can add or remove dependencies with `poetry add` and `poetry remove` respectively. To get into the environment use `poetry shell`.

**Note:** This will not work on Windows if using `pyuwsgi` as the HTTP server. It will work on WSL as a workaround. It'll also work in "production" mode if using the Cloud Run method below.

### Setup with Docker

If you don't have Docker installed, [install Docker](https://docs.docker.com/engine/install/).

Open a terminal in the project directory and create an image from the Dockerfile:

```
docker build --pull --rm -f Dockerfile -t pose-viewer-pilot:1.0.0 .
```

Then, create and run a container from the image:

```
docker run -d -p 8000:8000 --name pose-viewer-pilot --mount type=bind,source="%cd%"/app,target=/app/app pose-viewer-pilot:1.0.0
```

## Testing

### Testing with poetry

To run locally, drop into the environment:

```
poetry shell
```

Then:

```
uwsgi --http :8000 --master --processes 1 --threads 8 -w app.main:app
```

This will run a server in `http://127.0.0.1:8000`.

### Testing with Docker

Start the Docker image created in **Setup with Docker**:

```
docker start pose-viewer-pilot
```

This will run a server in `http://127.0.0.1:8000`.

## Testing with Cloud Run

Easiest way is to use the Cloud Code VSCode extension.

First, make sure `gcloud` CLI is installed.

Then, make sure you're logged in: `gcloud auth login` (will open browser)

And that the project is set: `gcloud config set project pose-viewer-pilot`

To install, open VSCode, <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd>, then search `Cloud Code`.

To run it, click the `</> Cloud Code` in the status bar at the bottom, or <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd>
and select **Cloud Code: Run on Cloud Run Emulator**.

This will run a server in `http://localhost:8080`.

## Deployment

Deployment is currently automatically set up to rebuild the image on push to `main` from the GCP side.

See: [Cloud Build Trigger](https://console.cloud.google.com/cloud-build/triggers?organizationId=284540140746&project=pose-viewer-pilot)

## Building pyscript

### Setup

To compile the pyscript files when not using the CDN version, follow these steps.

If `npm` is not installed:

```
conda install nodejs
```

(This works on Windows as well.)

Or:

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
nvm install node
```

### Compilation

```
git clone https://github.com/pyscript/pyscript.git
cd pyscript
cd pyscriptjs
npm install
rm -rf examples/build && npm run dev
```

Then copy the `examples/build` contents to your static assets, namely:

```
pyscript.css
pyscript.min.js
pyscript.min.js.map
```
