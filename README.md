# frappe_docker
[![Build Status](https://travis-ci.org/frappe/frappe_docker.svg?branch=master)](https://travis-ci.org/frappe/frappe_docker)

- [Docker](https://docker.com/) is an open source project to pack, ship and run any Linux application in a lighter weight, faster container than a traditional virtual machine.

- Docker makes it much easier to deploy [frappe](https://github.com/frappe/frappe) on your servers.

- This container uses [bench](https://github.com/frappe/bench) to install frappe.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

[Docker](https://www.docker.com/)

[Docker Compose](https://docs.docker.com/compose/overview/)

### Container Configuration

#### ports:

```
ports:
      - "3307:3307"   mariadb-port
      - "8000:8000"   webserver-port
      - "11000:11000" redis-cache
      - "12000:12000" redis-queue
      - "13000:13000" redis-socketio
      - "9000:9000"   socketio-port
      - "6787:6787"   file-watcher-port
```

Expose port 3307 inside the container on port 3307 on ALL local host interfaces. In order to bind to only one interface, you may specify the host's IP address as `([<host_interface>:[host_port]])|(<host_port>):<container_port>[/udp]` as defined in the [docker port binding documentation](http://docs.docker.com/userguide/dockerlinks/). The port 3307 of the mariadb container and port 8000 of the frappe container is exposed to the host machine and other containers.

#### volumes:

```
volumes:
     - ./frappe-bench:/home/frappe/frappe-bench
     - ./conf/mariadb-conf.d:/etc/mysql/conf.d
     - ./redis-conf/redis_socketio.conf:/etc/conf.d/redis.conf
     - ./redis-conf/redis_queue.conf:/etc/conf.d/redis.conf
     - ./redis-conf/redis_cache.conf:/etc/conf.d/redis.conf
```
Exposes a directory inside the host to the container.

#### links:

```
links:
      - redis-cache
      - redis-queue
      - redis-socketio
      - mariadb
```

Links allow you to define extra aliases by which a service is reachable from another service.

#### depends_on:

```
depends_on:
      - mariadb
      - redis-cache
      - redis-queue
      - redis-socketio
```
Express dependency between services, which has two effects:

1. docker-compose up will start services in dependency order. In the following example, mariadb and redis will be started before frappe.

2. docker-compose up SERVICE will automatically include SERVICE’s dependencies. In the following example, docker-compose up docker_frappe will also create and start mariadb and redis.

### Installation

#### 1. Installation Pre-requisites

- Install [Docker](https://docs.docker.com/engine/installation) Community Edition

- Install [Docker Compose](https://docs.docker.com/compose/install/) (only for Linux users). Docker for Mac, Docker for Windows, and Docker Toolbox include Docker Compose

#### 2. Build the container and install bench

* Clone this repo and change your working directory to frappe_docker
	
		git clone --depth 1 https://github.com/frappe/frappe_docker.git
		cd frappe_docker

* Build the container and install bench inside the container.

	1.Build the 5 linked containers frappe, mariadb, redis-cache, redis-queue and redis-socketio using this command. 	 Make sure your current working directory is frappe_docker which contains the docker-compose.yml and Dockerfile.
	It creates a user, frappe inside the frappe container, whose working directory is /home/frappe. It also clones
	the bench-repo from [here](https://github.com/frappe/bench)

		docker-compose up -d

	Note: Please do not remove the bench-repo directory the above commands will create



#### Basic Usage
1. Starting docker containers

	This command can be used to start containers

		docker-compose start

2. Accessing the frappe container via CLI

		docker exec -i -u root frappe bash -c "cd /home/frappe && chown -R frappe:frappe ./*"
		docker exec -it frappe bash

3. Create a new bench

	The init command will create a bench directory with frappe framework
	installed. It will be setup for periodic backups and auto updates once
	a day.
		
		cd .. && bench init frappe-bench --skip-bench-mkdir --skip-redis-config-generation && cd frappe-bench
		mv Procfile_docker Procfile && mv sites/common_site_config_docker.json sites/common_site_config.json

4. Set the db host for bench (points bench to the mariadb container) since the 3 containers are linked

		bench set-mariadb-host mariadb

5. Add a site (make sure your current path is /home/frappe/frappe-bench)

	Frappe apps are run by frappe sites and you will have to create at least one
	site. The new-site command allows you to do that.

		bench new-site site1.local

6. Add apps (make sure your current path is /home/frappe/frappe-bench)

	The get-app command gets remote frappe apps from a remote git repository and installs them. Example: [erpnext](https://github.com/frappe/erpnext)

		bench get-app erpnext https://github.com/frappe/erpnext

7. Install apps (make sure your current path is /home/frappe/frappe-bench)

	To install an app on your new site, use the bench `install-app` command.

		bench --site site1.local install-app erpnext

8. Start bench (make sure your current path is /home/frappe/frappe-bench)

	To start using the bench, use the `bench start` command

		bench start

9. Exiting the frappe container and stopping all the containers gracefully.

  		exit
  		docker-compose stop

10. Removing docker containers

		docker-compose rm

11. Removing dangling volumes

	The volume frappe on your  local machine is shared by the host(your local machine) and the frappe container.
	Please do not delete this volume from your local machine. Any changes made in this directory will reflect on both
	the container and the host. The below command specifies how to remain dangling volumes which may be taking up
	unecessary space on your host.

		docker volume rm $(docker volume ls -f dangling=true -q)

To login to Frappe / ERPNext, open your browser and go to `[your-external-ip]:8000`, probably `localhost:8000`

The default username is "Administrator" and password is what you set when you created the new site.

## Built With

* [Docker](https://www.docker.com/)

## Contributing

Feel free to contribute to this project and make the container better

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
