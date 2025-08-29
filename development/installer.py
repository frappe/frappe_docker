#!/usr/bin/env python3
import argparse
import os
import subprocess
import time
import socket
from typing import Tuple, Optional


def load_env_file(env_file_path: str = ".env") -> None:
    """Load environment variables from a .env file if it exists."""
    if os.path.exists(env_file_path):
        cprint(f"Loading environment variables from {env_file_path}", level=3)
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value


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


def check_database_connection(host, port, timeout=30):
    """
    Check if database service is reachable
    """
    cprint(f"Checking database connection to {host}:{port}...", level=3)
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                cprint(f"✓ Database is reachable at {host}:{port}", level=2)
                return True
                
        except Exception as e:
            pass
            
        cprint(f"→ Database not reachable. Waiting... ({int(time.time() - start_time)}s)", level=3)
        time.sleep(2)
    
    cprint(f"✗ Database connection timeout after {timeout}s", level=1)
    return False


def normalize_db_type(db_type: str) -> str:
    """
    Normalize database type to match Frappe's expected values.
    Frappe expects 'postgres' not 'postgresql'.
    """
    db_type = db_type.lower().strip()
    if db_type in ["postgresql", "postgres", "pg"]:
        return "postgres"
    elif db_type in ["mariadb", "mysql"]:
        return "mariadb"
    else:
        cprint(f"Warning: Unknown database type '{db_type}', defaulting to 'mariadb'", level=3)
        return "mariadb"


def get_database_config(args) -> Tuple[str, int, str, str]:
    """
    Get database configuration from args or environment variables.
    Returns: (host, port, username, password)
    """
    # Normalize database type to ensure compatibility with Frappe
    normalized_db_type = normalize_db_type(args.db_type)
    args.db_type = normalized_db_type
    
    # Set defaults based on database type
    if normalized_db_type == "postgres":
        default_host = os.getenv("POSTGRES_HOST", "db")
        default_port = int(os.getenv("POSTGRES_PORT", "5432"))
        default_username = os.getenv("POSTGRES_USER", "postgres")
        default_password = os.getenv("POSTGRES_PASSWORD", "123")
    else:  # mariadb/mysql
        default_host = os.getenv("MYSQL_HOST", "db")
        default_port = int(os.getenv("MYSQL_PORT", "3306"))
        default_username = os.getenv("MYSQL_USER", "root")
        default_password = os.getenv("MYSQL_ROOT_PASSWORD", "123")
    
    # Use command line args if provided, otherwise use defaults
    host = args.db_host or default_host
    port = args.db_port or default_port
    username = args.db_username or default_username
    password = args.db_password or default_password
    
    return host, port, username, password


def main():
    # Load environment variables from .env file if it exists
    load_env_file()
    
    parser = get_args_parser()
    args = parser.parse_args()
    
    # Display configuration summary
    cprint("=== Frappe Bench Setup Configuration ===", level=2)
    db_host, db_port, db_username, _ = get_database_config(args)
    cprint(f"Database Type: {args.db_type}", level=3)
    cprint(f"Database Host: {db_host}:{db_port}", level=3)
    cprint(f"Database User: {db_username}", level=3)
    cprint(f"Site Name: {args.site_name}", level=3)
    cprint(f"Bench Name: {args.bench_name}", level=3)
    cprint("=========================================", level=2)
    
    init_bench_if_not_exist(args)
    success = create_site_in_bench(args)
    if not success:
        cprint("Site creation failed. Please check the database connection and try again.", level=1)
        exit(1)


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
        help="frappe repo to use, default: version-15",  # noqa: E501
        default="version-15",
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
    parser.add_argument(
        "-a",
        "--admin-password",
        action="store",
        type=str,
        help="admin password for site, default: admin",  # noqa: E501
        default="123",
    )
    parser.add_argument(
        "-d",
        "--db-type",
        action="store",
        type=str,
        help="Database type to use (e.g., mariadb or postgres)",
        default="postgres",  # Changed to postgres for PostgreSQL setup
    )
    parser.add_argument(
        "--db-host",
        action="store",
        type=str,
        help="Database host, default: db (for Docker) or localhost",
        default=None,
    )
    parser.add_argument(
        "--db-port",
        action="store",
        type=int,
        help="Database port, default: 5432 for postgres, 3306 for mariadb",
        default=None,
    )
    parser.add_argument(
        "--db-username",
        action="store",
        type=str,
        help="Database username, default: postgres for postgres, root for mariadb",
        default=None,
    )
    parser.add_argument(
        "--db-password",
        action="store",
        type=str,
        help="Database password, default: 123",
        default=None,
    )
    parser.add_argument(
        "--db-name",
        action="store",
        type=str,
        help="Database name for the site (optional)",
        default=None,
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
        cprint("Set db_host", level=3)
        if args.db_type:
            cprint(f"Setting db_type to {args.db_type}", level=3)
            subprocess.call(
                ["bench", "set-config", "-g", "db_type", args.db_type],
                cwd=os.path.join(os.getcwd(), args.bench_name),
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
        cprint(
            "Set redis_socketio to redis://redis-queue:6379 for backward compatibility",  # noqa: E501
            level=3,
        )
        subprocess.call(
            [
                "bench",
                "set-config",
                "-g",
                "redis_socketio",
                "redis://redis-queue:6379",
            ],
            cwd=os.getcwd() + "/" + args.bench_name,
        )
        cprint("Set developer_mode", level=3)
        subprocess.call(
            ["bench", "set-config", "-gp", "developer_mode", "1"],
            cwd=os.getcwd() + "/" + args.bench_name,
        )
        
        # Configure additional PostgreSQL-specific settings if needed
        if args.db_type == "postgres":
            configure_postgres_settings(args)
            
    except subprocess.CalledProcessError as e:
        cprint(e.output, level=1)


def configure_postgres_settings(args):
    """Configure PostgreSQL-specific settings for the bench."""
    cprint("Configuring PostgreSQL-specific settings...", level=3)
    
    # Get database configuration
    db_host, db_port, db_username, db_password = get_database_config(args)
    
    # Set PostgreSQL connection parameters in common_site_config.json
    postgres_configs = [
        ("db_host", db_host),
        ("db_type", "postgres"),
    ]
    
    # Add port configuration if non-standard
    if db_port != 5432:
        postgres_configs.append(("db_port", str(db_port)))
    
    for config_key, config_value in postgres_configs:
        cprint(f"Setting {config_key} to {config_value}", level=3)
        subprocess.call(
            ["bench", "set-config", "-g", config_key, config_value],
            cwd=os.getcwd() + "/" + args.bench_name,
        )


def create_site_in_bench(args):
    # Get database configuration
    db_host, db_port, db_username, db_password = get_database_config(args)
    
    # Check database connectivity before proceeding
    if not check_database_connection(db_host, db_port):
        db_type_name = "PostgreSQL" if args.db_type == "postgres" else "MariaDB"
        cprint(f"Cannot connect to {db_type_name} database at {db_host}:{db_port}. Please ensure the database service is running.", level=1)
        cprint("If using Docker, run: docker-compose up -d db", level=3)
        return False
    
    # Set database host configuration
    cprint(f"Setting db_host to {db_host}", level=3)
    subprocess.call(
        ["bench", "set-config", "-g", "db_host", db_host],
        cwd=os.getcwd() + "/" + args.bench_name,
    )
    
    # Build new site command
    new_site_cmd = [
        "bench",
        "new-site",
        f"--db-root-username={db_username}",
        f"--db-host={db_host}",
        f"--db-type={args.db_type}",
        f"--db-root-password={db_password}",
        f"--admin-password={args.admin_password}",
    ]
    
    # Add database-specific options
    if args.db_type == "mariadb":
        new_site_cmd.append("--mariadb-user-host-login-scope=%")
    
    # Add custom database name if specified
    if args.db_name:
        new_site_cmd.append(f"--db-name={args.db_name}")
    
    # Add database port if non-standard
    if (args.db_type == "postgres" and db_port != 5432) or (args.db_type == "mariadb" and db_port != 3306):
        new_site_cmd.append(f"--db-port={db_port}")
    apps = os.listdir(f"{os.getcwd()}/{args.bench_name}/apps")
    apps.remove("frappe")
    for app in apps:
        new_site_cmd.append(f"--install-app={app}")
    new_site_cmd.append(args.site_name)
    cprint(f"Creating Site {args.site_name} ...", level=2)
    try:
        result = subprocess.call(
            new_site_cmd,
            cwd=os.getcwd() + "/" + args.bench_name,
        )
        if result == 0:
            cprint(f"✓ Site {args.site_name} created successfully!", level=2)
            return True
        else:
            cprint(f"✗ Site creation failed with exit code {result}", level=1)
            return False
    except subprocess.CalledProcessError as e:
        cprint(f"✗ Site creation failed: {e}", level=1)
        return False


if __name__ == "__main__":
    main()
