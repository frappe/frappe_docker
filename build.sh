export APPS_JSON_BASE64=$(base64 -i apps.json)

docker buildx build \
  --platform linux/amd64 \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=PYTHON_VERSION=3.11.9 \
  --build-arg=NODE_VERSION=18.20.2 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=onesrv/erpnext_de_crm:15.29.0 \
  --file=images/custom/Containerfile .


