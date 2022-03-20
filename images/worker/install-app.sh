#!/bin/bash
set -e
set -x

APP=$1 BRANCH=$2 GIT_URL=$3

cd /home/frappe/frappe-bench

if test "$BRANCH" && test "$GIT_URL"; then
  # Clone in case not copied manually
  git clone --depth 1 -b "$BRANCH" "$GIT_URL" "apps/$APP"
  rm -r "apps/$APP/.git"
fi

env/bin/pip install -e "apps/$APP"

echo "$APP" >>sites/apps.txt
