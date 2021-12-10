#!/bin/bash

set -e
set -x

get_tag() {
  tags=$(git ls-remote --refs --tags --sort='v:refname' "https://github.com/$1" "v$2.*")
  tag=$(echo "$tags" | tail -n1 | sed 's/.*\///')
  echo "$tag"
}

FRAPPE_VERSION=$(get_tag frappe/frappe "$VERSION")
ERPNEXT_VERSION=$(get_tag frappe/erpnext "$VERSION")

cat <<EOL >>"$GITHUB_ENV"
FRAPPE_VERSION=$FRAPPE_VERSION
ERPNEXT_VERSION=$ERPNEXT_VERSION
GIT_BRANCH=version-$VERSION
VERSION=$VERSION
EOL
