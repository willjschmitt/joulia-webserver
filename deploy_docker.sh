#!/bin/bash
# Deploys the application to Docker by building the docker image, and pushing it
# to Docker. Tags the image with the first 6 characters of the commit, "latest",
# and the Travis build number.
# Expects the following environment variables to be provided by travis:
#  * TRAVIS_COMMIT
#  * DOCKER_USERNAME
#  * DOCKER_PASSWORD
#  * TRAVIS_BUILD_NUMBER
echo "Deploying Docker image."

DOCKER_REPO="willjschmitt/joulia-webserver"
COMMIT="${TRAVIS_COMMIT}::6"

