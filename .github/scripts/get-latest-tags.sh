#!/bin/bash

set -e
set -x

get_tag() {
    tags=$(git ls-remote --refs --tags --sort='v:refname' https://github.com/$1 "v$2.*")
    tag=$(echo "$tags" | tail -n1 | sed 's/.*\///')
    echo "$tag"
}

FRAPPE_VERSION=$(get_tag frappe/frappe "$VERSION")
ERPNEXT_VERSION=$(get_tag frappe/erpnext "$VERSION")

# shellcheck disable=SC2086
echo "FRAPPE_VERSION=$FRAPPE_VERSION" >>$GITHUB_ENV
# shellcheck disable=SC2086
echo "ERPNEXT_VERSION=$ERPNEXT_VERSION" >>$GITHUB_ENV
# shellcheck disable=SC2086
echo "GIT_BRANCH=version-$VERSION" >>$GITHUB_ENV
# shellcheck disable=SC2086
echo "VERSION=$VERSION" >>$GITHUB_ENV
