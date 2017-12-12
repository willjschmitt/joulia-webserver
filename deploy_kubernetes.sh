#!/bin/bash
# This script deploys the new Docker image to kubernetes. The Docker deployment
# needs to be deployed prior to this script being called, or the Kubernetes
# image update will fail.

DOCKER_REPO="willjschmitt/joulia-webserver"
COMMIT="${TRAVIS_COMMIT::6}"

kubectl set image deployment/joulia-webserver "joulia-webserver=${DOCKER_REPO}:${COMMIT}"
