#!/bin/bash

# View ERPNext Logs Script
# Usage: ./logs.sh [service-number-or-name] [--tail[=N]]

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# Helper functions
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Navigate to production directory
cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" || exit 1

FOLLOW_MODE="follow"
TAIL_LINES=200
SERVICE_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tail)
      FOLLOW_MODE="tail"
      if [[ "${2:-}" =~ ^[0-9]+$ ]]; then
        TAIL_LINES=$2
        shift 2
        continue
      fi
      shift
      ;;
    --tail=*)
      FOLLOW_MODE="tail"
      VALUE="${1#*=}"
      [[ "$VALUE" =~ ^[0-9]+$ ]] || { echo_error "--tail expects an integer"; exit 1; }
      TAIL_LINES=$VALUE
      shift
      ;;
    --lines)
      [[ "${2:-}" =~ ^[0-9]+$ ]] || { echo_error "--lines expects an integer"; exit 1; }
      TAIL_LINES=$2
      FOLLOW_MODE="tail"
      shift 2
      ;;
    -h|--help)
      cat << EOF
Usage: $0 [service-number-or-name] [--tail[=N]]

Services:
  1 or backend       - Gunicorn backend
  2 or frontend      - Nginx frontend
  3 or websocket     - Socket.io service
  4 or queue-short   - Short queue worker
  5 or queue-long    - Long queue worker
  6 or scheduler     - Background scheduler
  7 or all           - All services

Flags:
  --tail[=N]         Show the last N (default 200) log lines and exit
  --lines N          Alias for --tail=N
  -h, --help         Show this help

Examples:
  $0                 # Interactive menu (follow)
  $0 backend         # Follow backend logs
  $0 backend --tail 50   # Show last 50 backend log lines
  $0 --tail          # Show last 200 lines for all services
EOF
      exit 0
      ;;
    *)
      SERVICE_ARG="$1"
      shift
      ;;
  esac
done

if [[ -z "$SERVICE_ARG" ]]; then
  if [[ "$FOLLOW_MODE" == "tail" ]]; then
    INPUT="all"
  else
    echo_info "Available services:"
    echo "  1. backend      2. frontend     3. websocket"
    echo "  4. queue-short  5. queue-long   6. scheduler   7. all"
    read -p "Enter number or name: " INPUT
  fi
else
  INPUT="$SERVICE_ARG"
fi

# Map input to service name
case "$INPUT" in
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
echo_info "Logs for: $SERVICE"
[ "$SERVICE" = "all" ] && SERVICE=""
if [[ "$FOLLOW_MODE" == "follow" ]]; then
  echo_info "Streaming (Ctrl+C to exit)"
  docker compose --project-name erpnext-production -f production.yaml logs -f $SERVICE
else
  docker compose --project-name erpnext-production -f production.yaml logs --tail "$TAIL_LINES" $SERVICE
fi