import frappe
import json
import redis
from rq import Worker
from check_connection import (
    check_mariadb,
    check_redis_cache,
    check_redis_queue,
    check_redis_socketio,
)

def main():
    check_mariadb(retry=1, delay=0, print_attempt=False)
    print("MariaDB Connected")
    check_redis_cache(retry=1, delay=0, print_attempt=False)
    print("Redis Cache Connected")
    check_redis_queue(retry=1, delay=0, print_attempt=False)
    print("Redis Queue Connected")
    check_redis_socketio(retry=1, delay=0, print_attempt=False)
    print("Redis SocketIO Connected")

    print("Health check successful")
    exit(0)

if __name__ == "__main__":
    main()
