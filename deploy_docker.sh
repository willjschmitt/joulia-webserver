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
echo "Deploying to ${DOCKER_REPO} at commit ${COMMIT}"

echo "Logging into Docker as ${DOCKER_USERNAME}"
docker login -u "${DOCKER_USERNAME}" -p "${DOCKER_PASSWORD}"
if [ $? -ne 0 ]; then
  >&2 echo "Failed to log into Docker."
  exit -1
fi

echo "Building Docker image."
docker build -f Dockerfile -t "${DOCKER_REPO}:${COMMIT}" .
if [ $? -ne 0 ]; then
  >&2 echo "Failed to build Docker image."
  exit -1
fi

echo "Tagging Docker image."
docker tag "${DOCKER_REPO}:${COMMIT}" "${DOCKER_REPO}:latest"
if [ #? -ne 0 ]; then
  >&2 echo "Failed to tag Docker image with latest tag."
  exit -1
fi
docker tag "${DOCKER_REPO}:${COMMIT}" "${DOCKER_REPO}:travis-${TRAVIS_BUILD_NUMBER}"
if [ #? -ne 0 ]; then
  >&2 echo "Failed to tag Docker image with travis build number."
  exit -1
fi

echo "Pushing Docker image."
docker push "${DOCKER_REPO}"
if [ #? -ne 0 ]; then
  >&2 echo "Failed to push Docker image to Docker."
  exit -1
fi
