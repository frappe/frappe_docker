#!/usr/bin/env python3
import argparse
import os
import subprocess


def cprint(*args, level: int = 1):
    """
    logs colorful messages
    level = 1 : RED
    level = 2 : GREEN
    level = 3 : YELLOW

    default level = 1
    """
    CRED = "\033[31m"
    CGRN = "\33[92m"
    CYLW = "\33[93m"
    reset = "\033[0m"
    message = " ".join(map(str, args))
    if level == 1:
        print(CRED, message, reset)  # noqa: T001, T201
    if level == 2:
        print(CGRN, message, reset)  # noqa: T001, T201
    if level == 3:
        print(CYLW, message, reset)  # noqa: T001, T201


def main():
    parser = get_args_parser()
    args = parser.parse_args()
    init_bench_if_not_exist(args)
    create_site_in_bench(args)


def get_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j",
        "--apps-json",
        action="store",
        type=str,
        help="Path to apps.json, default: apps-example.json",
        default="apps-example.json",
    )  # noqa: E501
    parser.add_argument(
        "-b",
        "--bench-name",
        action="store",
        type=str,
        help="Bench directory name, default: frappe-bench",
        default="frappe-bench",
    )  # noqa: E501
    parser.add_argument(
        "-s",
        "--site-name",
        action="store",
        type=str,
        help="Site name, should end with .localhost, default: development.localhost",  # noqa: E501
        default="development.localhost",
    )
    parser.add_argument(
        "-r",
        "--frappe-repo",
        action="store",
        type=str,
        help="frappe repo to use, default: https://github.com/frappe/frappe",  # noqa: E501
        default="https://github.com/frappe/frappe",
    )
    parser.add_argument(
        "-t",
        "--frappe-branch",
        action="store",
        type=str,
        help="frappe repo to use, default: version-14",  # noqa: E501
        default="version-14",
    )
    parser.add_argument(
        "-p",
        "--py-version",
        action="store",
        type=str,
        help="python version, default: Not Set",  # noqa: E501
        default=None,
    )
    parser.add_argument(
        "-n",
        "--node-version",
        action="store",
        type=str,
        help="node version, default: Not Set",  # noqa: E501
        default=None,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose output",  # noqa: E501
    )
    return parser


def init_bench_if_not_exist(args):
    if os.path.exists(args.bench_name):
        cprint("Bench already exists. Only site will be created", level=3)
        return

    try:
        env = os.environ.copy()
        if args.py_version:
            env["PYENV_VERSION"] = args.py_version
        init_command = ""
        if args.node_version:
            init_command = f"nvm use {args.node_version};"
        if args.py_version:
            init_command += f"PYENV_VERSION={args.py_version} "
        init_command += "bench init "
        init_command += "--skip-redis-config-generation "
        init_command += "--verbose " if args.verbose else " "
        init_command += f"--frappe-path={args.frappe_repo} "
        init_command += f"--frappe-branch={args.frappe_branch} "
        init_command += f"--apps_path={args.apps_json} "
        init_command += args.bench_name
        command = [
            "/bin/bash",
            "-i",
            "-c",
            init_command,
        ]
        subprocess.call(command, env=env, cwd=os.getcwd())
        cprint("Configuring Bench ...", level=2)
        cprint("Set db_host to mariadb", level=3)
        subprocess.call(
            ["bench", "set-config", "-g", "db_host", "mariadb"],
            cwd=os.getcwd() + "/" + args.bench_name,
        )
        cprint("Set redis_cache to redis://redis-cache:6379", level=3)
        subprocess.call(
            [
                "bench",
                "set-config",
                "-g",
                "redis_cache",
                "redis://redis-cache:6379",
            ],
            cwd=os.getcwd() + "/" + args.bench_name,
        )
        cprint("Set redis_queue to redis://redis-queue:6379", level=3)
        subprocess.call(
            [
                "bench",
                "set-config",
                "-g",
                "redis_queue",
                "redis://redis-queue:6379",
            ],
            cwd=os.getcwd() + "/" + args.bench_name,
        )
        cprint("Set redis_socketio to redis://redis-socketio:6379", level=3)
        subprocess.call(
            [
                "bench",
                "set-config",
                "-g",
                "redis_socketio",
                "redis://redis-socketio:6379",
            ],
            cwd=os.getcwd() + "/" + args.bench_name,
        )
        cprint("Set developer_mode", level=3)
        subprocess.call(
            ["bench", "set-config", "-gp", "developer_mode", "1"],
            cwd=os.getcwd() + "/" + args.bench_name,
        )
    except subprocess.CalledProcessError as e:
        cprint(e.output, level=1)


def create_site_in_bench(args):
    new_site_cmd = [
        "bench",
        "new-site",
        "--no-mariadb-socket",
        "--mariadb-root-password=123",
        "--admin-password=admin",
    ]
    apps = os.listdir(f"{os.getcwd()}/{args.bench_name}/apps")
    apps.remove("frappe")
    for app in apps:
        new_site_cmd.append(f"--install-app={app}")

    new_site_cmd.append(args.site_name)

    subprocess.call(
        new_site_cmd,
        cwd=os.getcwd() + "/" + args.bench_name,
    )


if __name__ == "__main__":
    main()
