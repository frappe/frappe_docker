docker-compose -f .devcontainer/docker-compose.yml up -d && docker exec -e \"TERM=xterm-256color\" -w /workspace/development -it devcontainer-frappe-1 bash
