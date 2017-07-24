# frappe_docker

Containerizing the frappe bench installation for a development environment

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Docker
docker-compose
```

### Installing

A step by step series of examples that tell you have to get a development env running
#### 1. Installation Pre-requisites

- Installing Docker Community Edition

```
Follow the steps given in https://docs.docker.com/engine/installation

The Docker version used by us is Docker version 17.06.0-ce, build 02c1d87
```
- Installing docker-compose

```
Follow the steps given in (Docker for Mac, Docker for Windows, and Docker Toolbox include Docker Compose) https://docs.docker.com/compose/install/

The docker-compose version used by us is docker-compose version 1.14.0, build c7bdf9e
```

#### 2. Build the container and install bench

* Make sure your logged in as root. Build the container and install bench inside the container as a **non root** user
  source build-container.sh
Note: Please do not remove the bench directory the above commands will create

#### Basic Usage
* Starting docker containers
  docker-compose start
  docker-compose stop

* Accessing the frappe container via CLI
  ./start-container.sh

* Set the db host for bench(points bench to the mariadb container)
  bench set-mariadb-host mariadb

* Create a new bench

	The init command will create a bench directory with frappe framework
	installed. It will be setup for periodic backups and auto updates once
	a day.

		bench init frappe-bench && cd frappe-bench

* Add a site

	Frappe apps are run by frappe sites and you will have to create at least one
	site. The new-site command allows you to do that.

		bench new-site site1.local

* Add apps

	The get-app command gets remote frappe apps from a remote git repository and installs them. Example: [erpnext](https://github.com/frappe/erpnext)

		bench get-app erpnext https://github.com/frappe/erpnext

* Install apps

	To install an app on your new site, use the bench `install-app` command.

		bench --site site1.local install-app erpnext

* Exiting the frappe container and stopping all the containers gracefully
  exit
  docker-compose stop

* Removing docker containers
  docker-compose rm

* Removing dangling volumes
  docker volume rm $(docker volume ls -f dangling=true -q)

To login to Frappe / ERPNext, open your browser and go to `[your-external-ip]:8000`, probably `localhost:8000`

	The default username is "Administrator" and password is what you set when you created the new site.

*

## Built With

* [Docker](https://www.docker.com/)

## Contributing

Feel free to contribute to this project and make the containers better

## Authors

* **Vishal Seshagiri**

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used - [Pratik Vyas](https://github.com/pdvyas)
* Inspiration - [Rushabh Mehta](https://github.com/rmehta)
