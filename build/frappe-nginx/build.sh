#!/bin/bash

function nodeCleanUp() {
    rm -fr node_modules
    yarn install --production=true
}

cd /home/frappe/frappe-bench/apps/frappe
yarn
yarn run production

if [[ "$GIT_BRANCH" =~ ^(version-12|version-11)$ ]]; then
    nodeCleanUp
else
    nodeCleanUp
    # remove this when frappe framework moves this to dependencies from devDependencies
    yarn add node-sass
fi
