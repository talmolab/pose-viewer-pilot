# pose-viewer-pilot

- [Cloud Run Project](https://console.cloud.google.com/run/detail/us-west1/pose-viewer-pilot/metrics?project=pose-viewer-pilot)


## Testing
To run locally, drop into the environment:
```
poetry shell
```
Then:
```
uvicorn app.main:app --reload
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

See: [Cloud Build Trigger](https://console.cloud.google.com/cloud-build/triggers/edit/7d372e87-7d22-41bf-8a82-de57c5e1894d?project=gcr-fastapi-pilot)

