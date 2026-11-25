#!/bin/bash
set -e
# This script configures X11 forwarding for Linux and macOS systems.
# It installs X11, Openbox (on Linux), and checks for XQuartz (on macOS).
# It also updates the sshd_config file to enable X11Forwarding and restarts the SSH service.

# Check if the script is running with root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Error: This script requires root privileges. Please run it as a superuser"
  exit 1
fi

# Function to restart SSH service (Linux)
restart_ssh_linux() {
  if command -v service >/dev/null 2>&1; then
    sudo service ssh restart
  else
    sudo systemctl restart ssh
  fi
}

# Function to restart SSH service (macOS)
restart_ssh_macos() {
  launchctl stop com.openssh.sshd
  launchctl start com.openssh.sshd
}

SSHD_CONFIG=/etc/ssh/sshd_config

# Only the global section (everything before the first "Match" line) is read
# or changed. Directives inside Match blocks are per-user/host overrides and
# are preserved. Keywords and values are case-insensitive, and a directive may
# be written "Keyword value" or "Keyword=value".

# Print the global X11Forwarding value sshd uses: the first uncommented one.
x11_forwarding_value() {
  awk '
    { line = $0; sub(/^[[:space:]]+/, "", line) }
    tolower(line) ~ /^match([[:space:]]|$)/ { exit }
    { split(line, f, /[[:space:]=]+/) }
    tolower(f[1]) == "x11forwarding" { print tolower(f[2]); exit }
  ' "$SSHD_CONFIG"
}

# Rewrite global X11Forwarding lines (commented or not) to "X11Forwarding yes".
enable_global_x11_forwarding() {
  local tmp rc
  tmp=$(mktemp)
  awk '
    { line = $0; sub(/^[[:space:]]+/, "", line) }
    tolower(line) ~ /^match([[:space:]]|$)/ { in_match = 1 }
    !in_match && tolower(line) ~ /^#?[[:space:]]*x11forwarding([[:space:]=]|$)/ {
      print "X11Forwarding yes"
      next
    }
    { print }
  ' "$SSHD_CONFIG" >"$tmp" && sudo cp "$tmp" "$SSHD_CONFIG"
  rc=$?
  rm -f "$tmp"
  return "$rc"
}

update_x11_forwarding() {
  if [ "$(x11_forwarding_value)" = "yes" ]; then
    echo "X11Forwarding is already set to 'yes' in $SSHD_CONFIG."
    return
  fi

  enable_global_x11_forwarding

  if [ "$(x11_forwarding_value)" != "yes" ]; then
    echo "Error: could not enable X11Forwarding in $SSHD_CONFIG. Add 'X11Forwarding yes' before any Match block manually."
    exit 1
  fi

  if [[ "$OSTYPE" == "linux-gnu" ]]; then
    restart_ssh_linux
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    restart_ssh_macos
  fi
}

# Determine the operating system
if [[ "$OSTYPE" == "linux-gnu" ]]; then
  # Linux
  if command -v startx >/dev/null 2>&1; then
    echo "X11 is already installed."
  else
    # Check which package manager is available and install
    if command -v apt-get >/dev/null 2>&1; then
      install_x11() { sudo apt-get update && sudo apt-get install -y xorg openbox; }
    elif command -v dnf >/dev/null 2>&1; then
      install_x11() { sudo dnf install -y xorg-x11-server-Xorg openbox; }
    else
      echo "Error: Unable to determine the package manager. Manual installation required."
      exit 1
    fi
    if install_x11; then
      echo "X11 and Openbox have been successfully installed."
    else
      echo "Error: Failed to install X11 and Openbox."
      exit 1
    fi
  fi

  # Call the function to update X11Forwarding
  update_x11_forwarding

  # Get the IP address of the host dynamically
  host_ip=$(hostname -I | awk '{print $1}')
  xhost + "$host_ip" && xhost + local:
  # Set the DISPLAY variable to the host IP
  export DISPLAY="$host_ip:0.0"
  echo "DISPLAY variable set to $DISPLAY"

elif [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  if command -v xquartz >/dev/null 2>&1; then
    echo "XQuartz is already installed."
  else
    echo "Error: XQuartz is required for X11 forwarding on macOS. Please install XQuartz manually."
    exit 1
  fi

  # Call the function to update X11Forwarding
  update_x11_forwarding

  # Export the DISPLAY variable for macOS
  export DISPLAY=:0
  echo "DISPLAY variable set to $DISPLAY"
else
  echo "Error: Unsupported operating system."
  exit 1
fi
