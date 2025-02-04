## Prerequisites

- podman
- podman-compose
- docker-compose

Podman (the POD MANager) is a tool for managing containers and images, volumes mounted into those containers, and pods made from groups of containers. It is available on the official repositories of many Linux distributions.

## Step 1

- Clone this repository and change the current directory to the downloaded folder
  ```cmd
    git clone https://github.com/frappe/frappe_docker
    cd frappe_docker
  ```

## Step 2

- Create `apps.json` file with custom apps listed in it
  ```json
  [
    {
      "url": "https://github.com/frappe/erpnext",
      "branch": "version-15"
    },
    {
      "url": "https://github.com/frappe/hrms",
      "branch": "version-15"
    },
    {
      "url": "https://github.com/frappe/helpdesk",
      "branch": "main"
    }
  ]
  ```
  Check the syntax of the file using `jq empty apps.json`
  ### Generate base64 string from JSON file:
  `cmd export APPS_JSON_BASE64=$(base64 -w 0 apps.json)`

## Step 3

- Building the custom image using podman

```ruby
  podman build \
   --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
   --build-arg=FRAPPE_BRANCH=version-15 \
   --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
   --tag=custom:15 \
   --file=images/layered/Containerfile .
```

### Note

- Make sure to use the same tag when you export a variable on the next step

## Step 4

- Using the image
- Export environment variables with image name, tag and pull_policy
  ```ruby
      export CUSTOM_IMAGE=custom
      export CUSTOM_TAG=15
      export PULL_POLICY=never
  ```
- Configuration of parameters used when starting the containers
  - create `.env` file copying from example.env (Read more on setting up environment variables [here](https://github.com/frappe/frappe_docker/blob/main/docs/environment-variables.md)

## Final step

- Creating a compose file
- ```ruby
   podman compose -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  config > ./docker-compose.yml
  ```
  ### NOTE
  - podman compose is just a wrapper, it uses docker-compose if it is available or podman-compose if not. podman-compose have an issue reading .env files ([Issue](https://github.com/containers/podman-compose/issues/475)) and might create an issue when running the containers.
- Creating pod and starting the containers
  - `podman-compose --in-pod=1 --project-name erpnext -f ./docker-compose.yml up -d`

## Creating sites and installing apps

- You can create sites from the backend container
  - `podman exec -ti erpnext_backend_1 /bin/bash`
    - `bench new-site myerp.net --mariadb-root-password 123456 --admin-password 123123`
    - `bench --site myerp.net install-app erpnext`

## Autostart pod

- Systemd is the best option on autostart pods when the system boots. Create a unit file in either `/etc/systemd/system` [for root user] or `~/.config/systemd/user` [for non-root user]

  ```ruby
    [Unit]
    Description=Podman system daemon service
    After=network-online.target

    [Service]
    #User=
    #Group=
    Type=oneshot
    ExecStart=podman pod start POD_NAME


    [Install]
    WantedBy=default.target

  ```

  **Note:** Replace POD_NAME with a created pod name while creating a pod. This is a basic systemd unit file to autostart pod, but multiple options can be used, refer to the man page for [systemd](https://man7.org/linux/man-pages/man1/init.1.html). For better management of containers, [Quadlet](https://docs.podman.io/en/v4.4/markdown/podman-systemd.unit.5.html) is the best option for ease of updating and tracing issues on each container.

## Troubleshoot

- If there is a network issue while building the image, you need to remove caches and restart again

  - `podman system reset`
  - `sudo rm -rf ~/.local/share/containers/ /var/lib/container ~/.caches/containers`

- Database issue when restarting the container
  - Execute the following commands from **backend** container
  - `mysql -uroot -padmin -hdb` (Note: put your db password in place of _admin_).
  - `SELECT User, Host FROM mysql.user;`
  - Change the IP address to %, e.g. `RENAME USER '_5e5899d8398b5f7b'@'172.18.0.7' TO '_5e5899d8398b5f7b'@'%'`
