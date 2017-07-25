# frappe_docker

* Docker Compose file to run frappe in a container
* Docker makes it much easier to deploy [frappe](https://github.com/frappe/frappe) on your development servers.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

[Docker](https://www.docker.com/)

[Docker Compose](https://docs.docker.com/compose/overview/)

### Container Configuration

#### ports:

```
ports:
      - "3306:3306"
      - "8000:8000"
```

Expose port 3306 inside the container on port 3306 on ALL local host interfaces. In order to bind to only one interface, you may specify the host's IP address as `([<host_interface>:[host_port]])|(<host_port>):<container_port>[/udp]` as defined in the [docker port binding documentation](http://docs.docker.com/userguide/dockerlinks/). The port 3306 of the mariadb container and port 8000 of the frappe container is exposed to the host machine and other containers.

#### volumes:

```
volumes:
     - ./frappe:/home/frappe
     - ./conf/mariadb-conf.d:/etc/mysql/conf.d
```
Exposes a directory inside the host to the container.

#### links:

```
links:
      - redis
      - mariadb
```

Links another container to the current container. This will add `--link docker_frappe:mariadb` and `--link docker_frappe:redis` to the options when running the container.

#### depends_on:

```
depends_on:
      - mariadb
      - redis
```
Express dependency between services, which has two effects:

1. docker-compose up will start services in dependency order. In the following example, mariadb and redis will be started before frappe.

2. docker-compose up SERVICE will automatically include SERVICE’s dependencies. In the following example, docker-compose up docker_frappe will also create and start mariadb and redis.

### Installation

#### 1. Installation Pre-requisites

- Installing Docker Community Edition (version 17.06.0-ce)

	Follow the steps given in [here](https://docs.docker.com/engine/installation)

- Installing Docker Compose (only for Linux users). Docker for Mac, Docker for Windows, and Docker Toolbox include Docker Compose (version 1.14.0)

	Follow the steps given in [here](https://docs.docker.com/compose/install/)

#### 2. Build the container and install bench

* Build the container and install bench inside the container as a **non root** user
	
	This command requests the user to enter a password for the MySQL root user, please remember it for future use.
	This command also builds the 3 linked containers docker-frappe, mariadb and redis using the docker-compose up -d, 
	it creates a user frappe inside the docker-frappe container, whose working directory is /home/frappe. It also clones
	the bench-repo from [here](https://github.com/frappe/bench)
		
		sudo source build-container.sh

	Note: Please do not remove the bench-repo directory the above commands will create

#### Basic Usage
1. Starting docker containers

	This command can be used to start containers
	
		sudo docker-compose start

2. Accessing the frappe container via CLI

		sudo ./docker-enter.sh
		
3. Create a new bench

	The init command will create a bench directory with frappe framework
	installed. It will be setup for periodic backups and auto updates once
	a day.

		bench init frappe-bench && cd frappe-bench		

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
  		sudo docker-compose stop

10. Removing docker containers

		sudo docker-compose rm

11. Removing dangling volumes
	
	The volume frappe on your  local machine is shared by the host(your local machine) and the frappe container.
	Please do not delete this volume from your local machine. Any changes made in this directory will reflect on both
	the container and the host. The below command specifies how to remain dangling volumes which may be taking up
	unecessary space on your host.
	
		sudo docker volume rm $(docker volume ls -f dangling=true -q)

To login to Frappe / ERPNext, open your browser and go to `[your-external-ip]:8000`, probably `localhost:8000`

The default username is "Administrator" and password is what you set when you created the new site.

## Built With

* [Docker](https://www.docker.com/)

## Contributing

Feel free to contribute to this project and make the container better

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
