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
# Any X11Forwarding line, commented or not, allowing leading whitespace.
X11_FORWARDING_LINE='^[[:space:]]*#?[[:space:]]*[Xx]11[Ff]orwarding([[:space:]=]|$).*'

# Print the X11Forwarding value sshd uses: the first uncommented directive.
# Keywords and values are case-insensitive; "Keyword value" or "Keyword=value".
x11_forwarding_value() {
  awk -F'[[:space:]=]+' '
    { sub(/^[[:space:]]+/, "") }
    tolower($1) == "x11forwarding" { print tolower($2); exit }
  ' "$SSHD_CONFIG"
}

update_x11_forwarding() {
  if [ "$(x11_forwarding_value)" = "yes" ]; then
    echo "X11Forwarding is already set to 'yes' in $SSHD_CONFIG."
    return
  fi

  if [[ "$OSTYPE" == "linux-gnu" ]]; then
    sudo sed -i -E "s/$X11_FORWARDING_LINE/X11Forwarding yes/" "$SSHD_CONFIG"
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    # BSD sed needs an explicit (empty) backup suffix after -i
    sudo sed -i '' -E "s/$X11_FORWARDING_LINE/X11Forwarding yes/" "$SSHD_CONFIG"
  fi

  if [ "$(x11_forwarding_value)" != "yes" ]; then
    echo "Error: could not enable X11Forwarding in $SSHD_CONFIG. Add 'X11Forwarding yes' manually."
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
