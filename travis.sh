#!/bin/bash

################# ./travis.sh #################
# This script takes care of the common steps 
# found in the frappe_docker Travis CI builds. 
#
#   Usage: [-a | -s | -w | -h] [-n <name of service>] [-t <tag> | -g <version number>] [-o]
#
# Argumets:
#
#   -a | --assets (exclusive): Build the nginx + static assets image
#   -s | --socketio (exclusive): Build the frappe-socketio image
#   -w | --worker (exclusive): Build the python environment image
#   -h | --help (exclusive): Print this page
#   
#   -n | --service <name of service>: Name of the service to build: "erpnext" or "frappe"
#     Note: --socketio does not respect this argument
#     Note: This will build an image with the name "$SERVICE-assets" (i.e. "erpnext-worker", "frappe-assets", etc.)
#
#   -t | --tag <tag> (exclusive): The image tag (i.e. erpnext-worker:$TAG )
#   -g | --git-version <version number> (exclusive): The version number of --service (i.e. "11", "12", etc.)
#     Note: This must be a number, not a string!
#
#   -o | --tag-only: Only tag an image and push it.
#
#


while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -a|--assets)
      ASSETS=1
      shift 
    ;;
    -g|--git-version)
      version="$2"
      shift
      shift
    ;;
    -h|--help)
      HELP=1
      shift
    ;;
    -n|--service)
      SERVICE="$2"
      shift
      shift 
    ;;
    -o|--tag-only)
      TAGONLY=1
      shift
    ;;
    -s|--socketio)
      SOCKETIO=1
      shift 
    ;;
    -t|--tag)
      TAG="$2"
      shift
      shift
    ;;
    -w|--worker)
      WORKER=1
      shift 
    ;;
    *)
      HELP=1
      shift
    ;;
  esac
done

function help() {
  echo "################ $0 #################"
  echo " This script takes care of the common steps found in the frappe_docker Travis CI builds."
  echo ""
  echo "   Usage: [-a | -s | -w | -h] [-n <name of service>] [-t <tag> | -g <version number>] [-o]"
  echo ""
  echo " Argumets:"
  echo ""
  echo "   -a | --assets (exclusive): Build the nginx + static assets image"
  echo "   -s | --socketio (exclusive): Build the frappe-socketio image"
  echo "   -w | --worker (exclusive): Build the python environment image"
  echo "   -h | --help (exclusive): Print this page"
  echo ""
  echo "   -n | --service <name of service>: Name of the service to build: \"erpnext\" or \"frappe\""
  echo "     Note: --socketio does not respect this argument"
  echo "     Note: This will build an image with the name \"\$SERVICE-assets\" (i.e. \"erpnext-worker\", \"frappe-assets\", etc.)"
  echo ""
  echo "   -t | --tag <tag> (exclusive): The image tag (i.e. erpnext-worker:\$TAG)"
  echo "   -g | --git-version <version number> (exclusive): The version number of --service (i.e. \"11\", \"12\", etc.)"
  echo "     Note: This must be a number, not a string!"
  echo ""
  echo "   -o | --tag-only: Only tag an image and push it."
}

function gitVersion() {
  echo "Pulling ${1} v${2}"
  git clone https://github.com/frappe/${1} --branch version-${2}
  cd ${1}
  git fetch --tags
  TAG=$(git tag --list --sort=-version:refname "v${2}*" | sed -n 1p | sed -e 's#.*@\(\)#\1#')
  cd ..
  DOCKERFILE="v${2}.Dockerfile"
}

function tagAndPush() {
  echo "Tagging ${1} as \"${2}\" and pushing"
  docker tag ${1} frappe/${1}:${2}
  docker push frappe/${1}:${2}
}

function build () {
  echo "Building ${1} ${3} image using ${4}"
  docker build -t ${1}-${3} -f build/${1}-${3}/${4:-Dockerfile} .
  tagAndPush "${1}-${3}" ${2}
}

if [[ HELP ]]; then
  help
  exit 1
fi

if [[ $VERSION ]]; then
  gitVersion $SERVICE $VERSION 
fi

DOCKERFILE=${DOCKERFILE:-Dockerfile}

if [[ $WORKER ]]; then
  if [[ $TAGONLY ]]; then
    tagAndPush "${SERVICE}-worker" ${TAG} 
  else 
    build $SERVICE $TAG worker ${DOCKERFILE} 
  fi
elif [[ $ASSETS ]]; then 
  if [[ $TAGONLY ]]; then
    tagAndPush "${SERVICE}-assets" ${TAG}
  else 
    build $SERVICE $TAG assets ${DOCKERFILE}
  fi
elif [[ $SOCKETIO ]]; then
  if [[ $TAGONLY ]]; then
    tagAndPush "frappe-socketio" ${TAG}
  else 
    build frappe $TAG socketio ${DOCKERFILE}
  fi
fi