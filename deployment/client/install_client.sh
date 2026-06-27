#!/bin/bash
echo "Installing CosmOS ERP Client..."
echo "Updating /etc/hosts... (requires sudo)"
SERVER_IP="127.0.0.1" 
if grep -q "cosmos.local" /etc/hosts; then
    echo "cosmos.local already exists."
else
    echo "$SERVER_IP cosmos.local" | sudo tee -a /etc/hosts
fi
mkdir -p $HOME/.local/share/icons
cp cosmos-icon.png $HOME/.local/share/icons/cosmos-icon.png
DESKTOP_FILE="$HOME/Desktop/CosmOS ERP.desktop"
cat <<EOD > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=CosmOS ERP
Comment=Enterprise Resource Planning System
Exec=xdg-open http://cosmos.local:8081
Icon=$HOME/.local/share/icons/cosmos-icon.png
Terminal=false
Categories=Office;Business;
EOD
chmod +x "$DESKTOP_FILE"
echo "Installation complete!"
