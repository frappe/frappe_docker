#!/bin/sh

set -e

# Update timestamp for ".build" file to enable caching assets:
# https://github.com/frappe/frappe/blob/52d8e6d952130eea64a9990b9fd5b1f6877be1b7/frappe/utils/__init__.py#L799-L805
if [ -d /usr/share/nginx/html/sites ]; then
  touch /usr/share/nginx/html/sites/.build -r /usr/share/nginx/html/.build
fi
