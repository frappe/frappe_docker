import socket, os, json, time
from six.moves.urllib.parse import urlparse

def is_open(ip, port, timeout=30):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()

def check_host(ip, port, retry=10, delay=3):
    ipup = False
    for i in range(retry):
        print("Attempt {i} to connect to {ip}:{port}".format(ip=ip,port=port,i=i+1))
        if is_open(ip, port):
            ipup = True
            break
        else:
            time.sleep(delay)
    return ipup

# Check connection to servers
config = None
try:
    with open('common_site_config.json') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise FileNotFoundError("common_site_config.json missing")
except:
    raise ValueError("common_site_config.json is not valid")

# Check mariadb
check_mariadb = False
check_mariadb = check_host(config.get('db_host', 'mariadb'), 3306)
if not check_mariadb:
    raise ConnectionError("Connection to mariadb timed out")

# Check redis queue
check_redis_queue = False
redis_queue_url = urlparse(config.get("redis_queue","redis://redis:6379")).netloc
redis_queue, redis_queue_port = redis_queue_url.split(":")
check_redis_queue = check_host(redis_queue, redis_queue_port)
if not check_redis_queue:
    raise ConnectionError("Connection to redis queue timed out")

# Check redis cache
check_redis_cache = False
redis_cache_url = urlparse(config.get("redis_cache","redis://redis:6379")).netloc
redis_cache, redis_cache_port = redis_cache_url.split(":")
check_redis_cache = check_host(redis_cache, redis_cache_port)
if not check_redis_cache:
    raise ConnectionError("Connection to redis cache timed out")

# Check redis socketio
check_redis_socketio = False
redis_socketio_url = urlparse(config.get("redis_socketio","redis://redis:6379")).netloc
redis_socketio, redis_socketio_port = redis_socketio_url.split(":")
check_redis_socketio = check_host(redis_socketio, redis_socketio_port)
if not check_redis_socketio:
    raise ConnectionError("Connection to redis socketio timed out")

print('Connections OK')
