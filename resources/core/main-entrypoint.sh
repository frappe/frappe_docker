#!/bin/bash
set -e

umask 0002

if ! whoami &>/dev/null; then
  if [ -w /etc/passwd ]; then
    user_name="default"
    if grep -q "^${user_name}:" /etc/passwd; then
      user_name="default_$(id -u)"
    fi
    echo "${user_name}:x:$(id -u):0:${user_name} user:${HOME:-/home/frappe}:/bin/bash" >>/etc/passwd
  fi
fi

ASSETS_PATH="/home/frappe/frappe-bench/sites/assets"
BAKED_PATH="/home/frappe/frappe-bench/assets"

echo "Linking fresh assets to volume..."
rm -rf "$ASSETS_PATH"
mkdir -p "$(dirname "$ASSETS_PATH")"
ln -s "$BAKED_PATH" "$ASSETS_PATH"

exec "$@"
