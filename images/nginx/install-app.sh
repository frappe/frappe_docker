#!/bin/bash
set -e
set -x

APP=$1 BRANCH=$2 GIT_URL=$3

cd /frappe-bench

if test "$BRANCH" && test "$GIT_URL"; then
  # Clone in case not copied manually
  git clone --depth 1 -b "$BRANCH" "$GIT_URL" "apps/$APP"
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

# Cleanup
rm -rf "apps/$APP"
rm -rf sites/assets
