#!/bin/bash

TAGS=$(git ls-remote --refs --tags --sort='v:refname' https://github.com/$REPO "v$VERSION.*")
TAG=$(echo $TAGS | tail -n1 | sed 's/.*\///')
echo $TAG
