#!/bin/bash
# Developer Note: Run this script in the /workspace/development directory

export NVM_DIR=~/.nvm
# shellcheck disable=SC1091
source $NVM_DIR/nvm.sh

sudo apt -qq update && sudo apt -qq install jq -y

get_client_apps() {
  apps=$(jq ".\"$client\"" apps.json)

  if [ "$apps" == "null" ]; then
    echo "No apps found for $client"
    exit 1
  fi
}

validate_bench_exists() {
  dir="$(pwd)/$bench_name"
  if [ -d "$dir" ]; then
    echo "Bench already exists. Only site will be created"
    is_existing_bench=true
  else
    is_existing_bench=false
  fi
}

validate_branch() {
  if [ "$app" == "frappe" ] || [ "$app" == "erpnext" ]; then
    if [ "$branch" != "develop" ] && [ "$branch" != "version-14" ] && [ "$branch" != "version-13" ]; then
      echo "Branch should be one of develop or version-14 or version-13"
      exit 1
    fi
  fi
}

validate_site() {
  if [[ ! "$site_name" =~ ^.*\.localhost$ ]]; then
    echo "Site name should end with .localhost"
    exit 1
  fi

  if [ "$is_existing_bench" = true ]; then
    validate_site_exists
  fi
}

validate_site_exists() {
  dir="$(pwd)/$bench_name/sites/$site_name"
  if [ -d "$dir" ]; then
    echo "Site already exists. Exiting"
    exit 1
  fi
}

validate_app_exists() {
  dir="$(pwd)/apps/$app"
  if [ -d "$dir" ]; then
    echo "App $app already exists."
    is_app_installed=true
  else
    is_app_installed=false
  fi
}

add_fork() {
  dir="$(pwd)/apps/$app"
  if [ "$fork" != "null" ]; then
    git -C "$dir" remote add fork "$fork"
  fi
}

install_apps() {
  initialize_bench=$1

  for row in $(echo "$apps" | jq -r '.[] | @base64'); do
    # helper function to retrieve values from dict
    _jq() {
      echo "${row}" | base64 --decode | jq -r "${1}"
    }

    app=$(_jq '.name')
    branch=$(_jq '.branch')
    upstream=$(_jq '.upstream')
    fork=$(_jq '.fork')

    if [ "$initialize_bench" = true ] && [ "$app" == "frappe" ]; then
      init_bench
    fi
    if [ "$initialize_bench" = false ]; then
      get_apps_from_upstream
    fi
  done
}

init_bench() {
  echo "Creating bench $bench_name"

  if [ "$branch" == "develop" ] || [ "$branch" == "version-14" ]; then
    python_version=python3.10
    PYENV_VERSION=3.10.5
    NODE_VERSION=v16
  elif [ "$branch" == "version-13" ]; then
    python_version=python3.9
    PYENV_VERSION=3.9.9
    NODE_VERSION=v14
  fi

  nvm use "$NODE_VERSION"
  PYENV_VERSION="$PYENV_VERSION" bench init --skip-redis-config-generation --frappe-branch "$branch" --python "$python_version" "$bench_name"
  cd "$bench_name" || exit

  echo "Setting up config"

  bench set-config -g db_host mariadb
  bench set-config -g redis_cache redis://redis-cache:6379
  bench set-config -g redis_queue redis://redis-queue:6379
  bench set-config -g redis_socketio redis://redis-socketio:6379

  ./env/bin/pip install honcho
}

get_apps_from_upstream() {
  validate_app_exists
  if [ "$is_app_installed" = false ]; then
    bench get-app --branch "$branch" --resolve-deps "$app" "$upstream" && add_fork
  fi

  if [ "$app" != "frappe" ]; then
    all_apps+=("$app")
  fi
}

echo "Client Name (from apps.json file)?"
read -r client && client=${client:-develop_client} && get_client_apps

echo "Bench Directory Name? (give name of existing bench to just create a new site) (default: frape-bench)"
read -r bench_name && bench_name=${bench_name:-frappe-bench} && validate_bench_exists

echo "Site Name? (should end with .localhost) (default: site1.localhost)"
read -r site_name && site_name=${site_name:-site1.localhost} && validate_site

if [ "$is_existing_bench" = true ]; then
  cd "$bench_name" || exit
else
  install_apps true
fi

echo "Getting apps from upstream for $client"
all_apps=() && install_apps false

echo "Creating site $site_name"
bench new-site "$site_name" --mariadb-root-password 123 --admin-password admin --no-mariadb-socket

echo "Installing apps to $site_name"
bench --site "$site_name" install-app "${all_apps[@]}"

bench --site "$site_name" set-config developer_mode 1
bench --site "$site_name" clear-cache
