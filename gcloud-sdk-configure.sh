#!/bin/bash -e
# Configures and connects to Google Cloud SDK using encrypted client secret.

gcloud auth activate-service-account --key-file "${GCLOUD_APPLICATION_CREDENTIALS}"
gcloud config set project "${GCLOUD_PROJECT_ID}"
gcloud config set compute/zone "${GCLOUD_ZONE}"

gcloud container clusters get-credentials "${GCLOUD_CLUSTER_NAME}"
