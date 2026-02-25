#!/usr/bin/env bash

print_manual_gum_install_guidance() {
  echo "Install gum manually: https://github.com/charmbracelet/gum#installation"
  echo "If installed into ~/.local/bin, add it to PATH first."
}

print_docker_install_guidance() {
  echo "Install Docker first: https://docs.docker.com/get-started/get-docker/"
}

print_docker_compose_install_guidance() {
  echo "This script requires Docker Compose v2 via the 'docker compose' command."
  echo "Docker Desktop includes it by default."
  echo "On Linux Engine-only setups, install the Docker Compose CLI plugin package (commonly 'docker-compose-plugin')."
  echo "Setup docs:"
  echo "https://docs.docker.com/compose/install/"
  echo "Note: this script uses 'docker compose' (Compose v2), not the old standalone 'docker-compose'."
}

print_docker_daemon_start_guidance() {
  echo "Start the Docker daemon/service and retry."
  echo "If you use Docker Desktop, ensure it is running."
}

print_docker_command_support_guidance() {
  echo "Update Docker to a recent version and ensure Compose v2 is available as 'docker compose'."
  echo "Standard 'docker' and 'docker compose' commands are required."
}
