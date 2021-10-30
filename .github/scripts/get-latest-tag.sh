#!/bin/bash

TAGS=$(git ls-remote --refs --tags --sort='v:refname' https://github.com/$REPO "v$VERSION.*")
TAG=$(echo $TAGS | tail -n1 | sed 's/.*\///')

echo "GIT_TAG=$TAG" >> $GITHUB_ENV
echo "GIT_BRANCH=version-$VERSION" >> $GITHUB_ENV
echo "VERSION=$VERSION" >> $GITHUB_ENV