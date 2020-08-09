# Custom apps

To add your own Frappe/ERPNext apps to the image, we'll need to create a custom image with the help of a unique wrapper script

> For the sake of simplicity, in this example, we'll be using a place holder called `[custom]`, and we'll be building off the edge image.

Create two directories called `[custom]-worker` and `[custom]-nginx` in the `build` directory.

```shell
cd frappe_docker
mkdir ./build/[custom]-worker ./build/[custom]-nginx
```

Create a `Dockerfile` in `./build/[custom]-worker` with the following content:

```Dockerfile
FROM frappe/erpnext-worker:edge

RUN install_app [custom] https://github.com/[username]/[custom] [branch]
# Only add the branch if you are using a specific tag or branch.
```

**Note:** Replace `https://github.com/[username]/[custom]` above with your custom app's Git repository URL (may include credentials if needed). Your custom app Git repository **must** be named exactly as the custom app's name, and use the same branch name as Frappe/ERPNext branch name that you use.

Create a `Dockerfile` in `./build/[custom]-nginx` with the following content:

```Dockerfile
FROM bitnami/node:12-prod

COPY build/[custom]-nginx/install_app.sh /install_app

RUN /install_app [custom] https://github.com/[username]/[custom] [branch]

FROM frappe/erpnext-nginx:edge

COPY --from=0 /home/frappe/frappe-bench/sites/ /var/www/html/
COPY --from=0 /rsync /rsync
RUN echo -n "\n[custom]" >> /var/www/html/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
```

Copy over the `install_app.sh` file from `./build/erpnext-nginx`

```shell
cp ./build/erpnext-nginx/install.sh ./build/[custom]-nginx
```

Open up `./installation/docker-compose-custom.yml` and replace all instances of `[app]` with the name of your app.

```shell
sed -i "s#\[app\]#[custom]#" ./installation/docker-compose-custom.yml
```

Install like usual, except that when you set the `INSTALL_APPS` variable to `erpnext,[custom]`.
