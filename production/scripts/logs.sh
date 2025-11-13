#!/bin/bash

# View ERPNext Logs Script
# Usage: ./logs.sh [service-number-or-name]

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# Helper functions
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Navigate to production directory
cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" || exit 1

# Show menu only if no argument provided
if [ -z "$1" ]; then
    echo_info "Available services:"
    echo "  1. backend      2. frontend     3. websocket"
    echo "  4. queue-short  5. queue-long   6. scheduler   7. all"
    read -p "Enter number or name: " INPUT
else
    INPUT=$1
fi

# Map input to service name
case "$INPUT" in
    -h|--help)
        cat << EOF
Usage: $0 [service-number-or-name]

Services:
  1 or backend       - Gunicorn backend
  2 or frontend      - Nginx frontend
  3 or websocket     - Socket.io service
  4 or queue-short   - Short queue worker
  5 or queue-long    - Long queue worker
  6 or scheduler     - Background scheduler
  7 or all           - All services

Examples:
  $0                 # Interactive menu
  $0 1               # View backend logs
  $0 backend         # Same as above
  $0 all             # View all logs
EOF
        exit 0
        ;;
    1|backend) SERVICE="backend" ;;
    2|frontend) SERVICE="frontend" ;;
    3|websocket) SERVICE="websocket" ;;
    4|queue-short) SERVICE="queue-short" ;;
    5|queue-long) SERVICE="queue-long" ;;
    6|scheduler) SERVICE="scheduler" ;;
    7|all) SERVICE="all" ;;
    *) echo_error "Invalid: $INPUT. Use 1-7 or service name."; exit 1 ;;
esac

# Check if services are running
docker ps | grep -q "erpnext-production" || { echo_error "ERPNext is not running!"; exit 1; }

# Show logs
echo_info "Logs for: $SERVICE (Ctrl+C to exit)"
[ "$SERVICE" = "all" ] && SERVICE=""
docker compose --project-name erpnext-production -f production.yaml logs -f $SERVICE