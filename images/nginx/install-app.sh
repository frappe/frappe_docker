#!/bin/bash
set -e
set -x

APP=$1

cleanup() {
  rm -rf "apps/$APP"
  rm -rf sites/assets/*
}

cd /frappe-bench

if ! test -d "apps/$APP/$APP/public"; then
  cleanup
  exit 0
fi

# Add all not built assets
cp -r "apps/$APP/$APP/public" "/out/assets/$APP"

# Add production node modules
yarn --cwd "apps/$APP" --prod
cp -r "apps/$APP/node_modules" "/out/assets/$APP/node_modules"

# Add built assets
yarn --cwd "apps/$APP"
echo "$APP" >>sites/apps.txt
yarn --cwd apps/frappe run production --app "$APP"
cp -r sites/assets /out

cleanup
