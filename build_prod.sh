#!/bin/bash
# docker container prune -f;docker image prune -f
VERSION=`git describe --tags $(git rev-list --tags --max-count=1)`
# In case of doubt on the image sanity or if you have time, uncomment below
#NO_CACHE=--no-cache
# In case you need full output of commands, e.g. for ensuring python packages version, uncomment below
#export BUILDKIT_PROGRESS=plain
# Preliminary, log using ecotaxa docker account
#docker login -u ecotaxa
# Build
docker build $NO_CACHE -t ecotaxa/zooprocess_v10 --progress=plain .
# Publish
docker tag ecotaxa/zooprocess_v10:latest ecotaxa/zooprocess_v10:$VERSION
docker push ecotaxa/zooprocess_v10:$VERSION
docker push ecotaxa/zooprocess_v10:latest
