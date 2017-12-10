#!/usr/bin/env bash
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

echo "Logging into Docker"
docker login -u "${DOCKER_USERNAME}" -p "${DOCKER_PASSWORD}"
if [ $? -ne 0 ]; then
  echo "Failed to log into Docker."
fi

echo "Building Docker image."
docker build -f Dockerfile -t "${DOCKER_REPO}:${COMMIT}" .
if [ $? -ne 0 ]; then
  echo "Failed to build Docker image."
fi

echo "Tagging Docker image."
docker tag "${DOCKER_REPO}:${COMMIT}" "${DOCKER_REPO}:latest"
if [ #? -ne 0 ]; then
  echo "Failed to tag Docker image with latest tag."
fi
docker tag "${DOCKER_REPO}:${COMMIT}" "${DOCKER_REPO}:travis-${TRAVIS_BUILD_NUMBER}"
if [ #? -ne 0 ]; then
  echo "Failed to tag Docker image with travis build number."
fi

echo "Pushing Docker image."
docker push "${DOCKER_REPO}"
if [ #? -ne 0 ]; then
  echo "Failed to push Docker image to Docker."
fi
