import socket
import json
import time
from six.moves.urllib.parse import urlparse

COMMON_SITE_CONFIG_FILE = 'common_site_config.json'
REDIS_QUEUE_KEY = 'redis_queue'
REDIS_CACHE_KEY = 'redis_cache'
REDIS_SOCKETIO_KEY = 'redis_socketio'
DB_HOST_KEY = 'db_host'
DB_PORT_KEY = 'db_port'
DB_PORT = 3306


def is_open(ip, port, timeout=30):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except Exception:
        return False
    finally:
        s.close()


def check_host(ip, port, retry=10, delay=3, print_attempt=True):
    ipup = False
    for i in range(retry):
        if print_attempt:
            print("Attempt {i} to connect to {ip}:{port}".format(ip=ip, port=port, i=i+1))
        if is_open(ip, port):
            ipup = True
            break
        else:
            time.sleep(delay)
    return ipup


# Check connection to servers
def get_config():
    config = None
    try:
        with open(COMMON_SITE_CONFIG_FILE) as config_file:
            config = json.load(config_file)
    except FileNotFoundError as exception:
        print(exception)
        exit(1)
    except Exception:
        print(COMMON_SITE_CONFIG_FILE+" is not valid")
        exit(1)
    return config


# Check service
def check_service(
    retry=10,
    delay=3,
    print_attempt=True,
    service_name=None,
    service_port=None):

    config = get_config()
    if not service_name:
        service_name = config.get(DB_HOST_KEY, 'mariadb')
    if not service_port:
        service_port = config.get(DB_PORT_KEY, DB_PORT)

    is_db_connected = False
    is_db_connected = check_host(
        service_name,
        service_port,
        retry,
        delay,
        print_attempt)
    if not is_db_connected:
        print("Connection to {service_name}:{service_port} timed out".format(
            service_name=service_name,
            service_port=service_port,
        ))
        exit(1)


# Check redis queue
def check_redis_queue(retry=10, delay=3, print_attempt=True):
    check_redis_queue = False
    config = get_config()
    redis_queue_url = urlparse(config.get(REDIS_QUEUE_KEY, "redis://redis-queue:6379")).netloc
    redis_queue, redis_queue_port = redis_queue_url.split(":")
    check_redis_queue = check_host(
        redis_queue,
        redis_queue_port,
        retry,
        delay,
        print_attempt)
    if not check_redis_queue:
        print("Connection to redis queue timed out")
        exit(1)


# Check redis cache
def check_redis_cache(retry=10, delay=3, print_attempt=True):
    check_redis_cache = False
    config = get_config()
    redis_cache_url = urlparse(config.get(REDIS_CACHE_KEY, "redis://redis-cache:6379")).netloc
    redis_cache, redis_cache_port = redis_cache_url.split(":")
    check_redis_cache = check_host(
        redis_cache,
        redis_cache_port,
        retry,
        delay,
        print_attempt)
    if not check_redis_cache:
        print("Connection to redis cache timed out")
        exit(1)


# Check redis socketio
def check_redis_socketio(retry=10, delay=3, print_attempt=True):
    check_redis_socketio = False
    config = get_config()
    redis_socketio_url = urlparse(config.get(REDIS_SOCKETIO_KEY, "redis://redis-socketio:6379")).netloc
    redis_socketio, redis_socketio_port = redis_socketio_url.split(":")
    check_redis_socketio = check_host(
        redis_socketio,
        redis_socketio_port,
        retry,
        delay,
        print_attempt)
    if not check_redis_socketio:
        print("Connection to redis socketio timed out")
        exit(1)


# Get site_config.json
def get_site_config(site_name):
    site_config = None
    with open('{site_name}/site_config.json'.format(site_name=site_name)) as site_config_file:
        site_config = json.load(site_config_file)
    return site_config


def main():
    check_service()
    check_redis_queue()
    check_redis_cache()
    check_redis_socketio()
    print('Connections OK')


if __name__ == "__main__":
    main()
