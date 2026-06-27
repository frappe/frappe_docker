# CosmOS ERP Deployment Guide

This folder contains all necessary files to install the CosmOS ERP server and client.

## 🚀 Server Installation
1. Copy the `server` folder to your server.
2. Open a terminal in the `server` folder.
3. Run the setup script:
   ```bash
   sudo ./setup.sh
   ```
*Note: Ensure you have Docker installed and the image `custom/cosmos:v16.23.2` available.*

## 💻 Client Installation
1. Copy the `client` folder to the client machine.
2. Open a terminal in the `client` folder.
3. Run the installation script:
   ```bash
   sudo ./install_client.sh
   ```
*Note: This script updates the /etc/hosts file and creates a desktop shortcut.*

## 🔗 Accessing the App
Open your browser and go to: `http://cosmos.local:8081`
