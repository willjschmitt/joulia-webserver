#!/usr/bin/env bash -e
# Deploys the application to Docker by building the docker image, and pushing it
# to Docker. Tags the image with the first 6 characters of the commit, "latest",
# and the Travis build number.
# Expects the following environment variables to be provided by travis:
#  * TRAVIS_COMMIT
#  * DOCKER_USERNAME
#  * DOCKER_PASSWORD
#  * TRAVIS_BUILD_NUMBER
DOCKER_REPO="willjschmitt/joulia-webserver"
COMMIT="${TRAVIS_COMMIT}::6"

docker login -u "${DOCKER_USERNAME}" -p "${DOCKER_PASSWORD}"
docker build -f Dockerfile -t "${DOCKER_REPO}:${COMMIT}" .
docker tag "${DOCKER_REPO}:${COMMIT}" "${DOCKER_REPO}:latest"
docker tag "${DOCKER_REPO}:${COMMIT}" "${DOCKER_REPO}:travis-${TRAVIS_BUILD_NUMBER}"
docker push "${DOCKER_REPO}"
