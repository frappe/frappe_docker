#!/bin/bash

################# travis.sh #################
# This script takes care of the common steps 
# found in the Travis CI builds. 

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
    -g|--git-branch)
      BRANCH="$2"
      shift
      shift 
    ;;
  esac
done

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

if [[ $BRANCH ]]; then
  gitVersion $NAME $BRANCH 
fi

DOCKERFILE=${DOCKERFILE:-Dockerfile}

if [[ $WORKER ]]; then
  if [[ $TAGONLY ]]; then
    tagAndPush "${NAME}-worker" ${TAG} 
  else 
    build $NAME $TAG worker ${DOCKERFILE} 
  fi
elif [[ $ASSETS ]]; then 
  if [[ $TAGONLY ]]; then
    tagAndPush "${NAME}-assets" ${TAG}
  else 
    build $NAME $TAG assets ${DOCKERFILE}
  fi
elif [[ $SOCKETIO ]]; then
  if [[ $TAGONLY ]]; then
    tagAndPush "${NAME}-socketio" ${TAG}
  else 
    build $NAME $TAG socketio ${DOCKERFILE}
  fi
fi