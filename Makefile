# makefile for manual installing

start:
    @docker-compose -f .devcontainer/docker-compose.yml up -d

restart:
    @docker-compose -f .devcontainer/docker-compose.yml stop
    @docker-compose -f .devcontainer/docker-compose.yml start

tty:
    @docker exec -e "TERM=xterm-256color" -w /workspace/development -it devcontainer_frappe_1 bash

clean:
    @docker-compose -f .devcontainer/docker-compose.yml down
    @docker volume prune
    @docker-compose -f .devcontainer/docker-compose.yml up -d
