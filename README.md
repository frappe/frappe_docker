# Docker_frappe

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

Installing Docker Community Edition 

```
Follow the steps given in https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/

The Docker version used by us is Docker version 17.06.0-ce, build 02c1d87
```
Installing docker-compose 

```
Follow the steps given in https://docs.docker.com/compose/install/

The docker-compose version used by us is docker-compose version 1.14.0, build c7bdf9e
```

Steps to be followed to build and run the docker image are :
```
1. Run the bash script bash_script.sh (Modify it to executable if not already given using the chmod +x command) with the command ./bash_script.sh
2. After a few minutes the prompt will point to the App container with a root prefix to it (your current location is /home/frappe)
3. You will be inside /home/frappe/code folder
4. Make the bash_run_container.sh executable by chmod +x as in step 1 and run it with the command ./bash_run_container.sh
5. Run the bash_for_container.sh file with the command ./bash_for_container.sh
6. You will be prompted to enter the Mysql db password it is 123
7. You will be prompted to choose and enter an administrator password please enter and remember it for future use
8. Once all the installation steps are complete you can access the Web based GUI by typing localhost:8000 on your browser.
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Docker](https://www.docker.com/)

## Contributing

Feel free to contribute to this and make the process better

## Authors

* **Vishal Seshagiri** - *Initial work* - [FrappeBench](https://github.com/frappe/bench)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used - Pratik Vyas(https://github.com/pdvyas)
* Inspiration - [Rushabh Mehta](https://github.com/rmehta)

