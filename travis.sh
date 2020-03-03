#!/bin/bash

################# travis.sh #################
# This script takes care of the common steps 
# found in the Travis CI builds. 

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -t|--tag)
      TAG="$2"
      shift
      shift
    ;;
    -w|--worker)
      WORKER=1
      shift 
    ;;
    -a|--assets)
      ASSETS=1
      shift 
    ;;
    -s|--socketio)
      SOCKETIO=1
      shift 
    ;;
    -n|--name)
      NAME="$2"
      shift
      shift 
    ;;
    -o|--tag-only)
      TAGONLY=1
      shift
    ;;
    *)    # unknown option
      POSITIONAL+=("$1") # save it in an array for later
      shift # past argument
    ;;
  esac
done

function tagAndPush() {
  echo "Tagging ${1} as \"${2}\" and pushing"
  docker tag ${1} frappe/${1}:${2}
  docker push frappe/${1}:${2}
}

function build () {
  echo "Building ${1} ${3} image"
  docker build -t ${1}-${3} -f build/${1}-worker/Dockerfile .
  tagAndPush "${1}-${3}" ${2}
}

if [[ $WORKER ]]; then
  if [[ $TAGONLY ]]; then
    tagAndPush "${NAME}-worker" ${TAG}
  else 
    build $NAME $TAG worker
  fi
elif [[ $ASSETS ]]; then 
  if [[ $TAGONLY ]]; then
    tagAndPush "${NAME}-assets" ${TAG}
  else 
    build $NAME $TAG assets
  fi
elif [[ $SOCKETIO ]]; then
  if [[ $TAGONLY ]]; then
    tagAndPush "${NAME}-socketio" ${TAG}
  else 
    build $NAME $TAG socketio
  fi
fi