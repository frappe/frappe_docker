WARNING: Do not use this in production if the site is going to be served over plain http.

### Step 1

Remove the traefik service from docker-compose.yml

### Step 2

Create nginx config file `/opt/nginx/conf/serve-8001.conf`:

```
server {
	listen 8001;
	server_name $http_host;

	location / {

 		rewrite ^(.+)/$ $1 permanent;
  		rewrite ^(.+)/index\.html$ $1 permanent;
  		rewrite ^(.+)\.html$ $1 permanent;

		proxy_set_header X-Frappe-Site-Name mysite.localhost;
		proxy_set_header Host mysite.localhost;
		proxy_pass  http://erpnext-nginx;
	}
}
```

Notes:

- Replace the port with any port of choice e.g. `listen 4200;`
- Change `mysite.localhost` to site name
- Repeat the server blocks for multiple ports and site names to get the effect of port based multi tenancy

### Step 3

Run the docker container

```shell
docker run --network=<project-name>_default \
  -p 8001:8001 \
  --volume=/opt/nginx/conf/serve-8001.conf:/etc/nginx/conf.d/default.conf -d nginx
```

Note: Change the volumes, network and ports as needed

With the above example configured site will be accessible on `http://localhost:8001`
