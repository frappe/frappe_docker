import argparse

from check_connection import (
    check_service,
    check_redis_cache,
    check_redis_queue,
    check_redis_socketio,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p',
        '--ping-service',
        dest='ping_services',
        action='append',
        type=str,
        help='list of services to ping, e.g. doctor -p "postgres:5432" --ping-service "mariadb:3306"',
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    check_service(retry=1, delay=0, print_attempt=False)
    print("Bench database Connected")
    check_redis_cache(retry=1, delay=0, print_attempt=False)
    print("Redis Cache Connected")
    check_redis_queue(retry=1, delay=0, print_attempt=False)
    print("Redis Queue Connected")
    check_redis_socketio(retry=1, delay=0, print_attempt=False)
    print("Redis SocketIO Connected")

    if(args.ping_services):
        for service in args.ping_services:
            service_name = None
            service_port = None

            try:
                service_name, service_port = service.split(':')
            except ValueError:
                print('Service should be in format host:port, e.g postgres:5432')
                exit(1)

            check_service(
                retry=1,
                delay=0,
                print_attempt=False,
                service_name=service_name,
                service_port=service_port,
            )
            print("{0}:{1} Connected".format(service_name, service_port))

    print("Health check successful")
    exit(0)


if __name__ == "__main__":
    main()
