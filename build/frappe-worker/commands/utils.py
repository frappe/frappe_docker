import json
import os
import subprocess
import boto3
import git

from frappe.installer import update_site_config
from constants import (
    APP_VERSIONS_JSON_FILE,
    APPS_TXT_FILE,
    COMMON_SITE_CONFIG_FILE
)

def run_command(command, stdout=None, stdin=None, stderr=None):
    stdout = stdout or subprocess.PIPE
    stderr = stderr or subprocess.PIPE
    stdin = stdin or subprocess.PIPE
    process = subprocess.Popen(command, stdout=stdout, stdin=stdin, stderr=stderr)
    out, error = process.communicate()
    if process.returncode:
        print("Something went wrong:")
        print(f"return code: {process.returncode}")
        print(f"stdout:\n{out}")
        print(f"\nstderr:\n{error}")
        exit(process.returncode)


def save_version_file(versions):
    with open(APP_VERSIONS_JSON_FILE, 'w') as f:
        return json.dump(versions, f, indent=1, sort_keys=True)


def get_apps():
    apps = []
    try:
        with open(APPS_TXT_FILE) as apps_file:
            for app in apps_file.readlines():
                if app.strip():
                    apps.append(app.strip())

    except FileNotFoundError as exception:
        print(exception)
        exit(1)
    except Exception:
        print(APPS_TXT_FILE + " is not valid")
        exit(1)

    return apps


def get_container_versions(apps):
    versions = {}
    for app in apps:
        try:
            version = __import__(app).__version__
            versions.update({app: version})
        except Exception:
            pass

        try:
            path = os.path.join('..', 'apps', app)
            repo = git.Repo(path)
            commit_hash = repo.head.object.hexsha
            versions.update({app+'_git_hash': commit_hash})
        except Exception:
            pass

    return versions


def get_version_file():
    versions = None
    try:
        with open(APP_VERSIONS_JSON_FILE) as versions_file:
            versions = json.load(versions_file)
    except Exception:
        pass
    return versions


def get_config():
    config = None
    try:
        with open(COMMON_SITE_CONFIG_FILE) as config_file:
            config = json.load(config_file)
    except FileNotFoundError as exception:
        print(exception)
        exit(1)
    except Exception:
        print(COMMON_SITE_CONFIG_FILE + " is not valid")
        exit(1)
    return config


def get_site_config(site_name):
    site_config = None
    with open('{site_name}/site_config.json'.format(site_name=site_name)) as site_config_file:
        site_config = json.load(site_config_file)
    return site_config


def save_config(config):
    with open(COMMON_SITE_CONFIG_FILE, 'w') as f:
        return json.dump(config, f, indent=1, sort_keys=True)


def get_password(env_var, default=None):
    return os.environ.get(env_var) or get_password_from_secret(f"{env_var}_FILE") or default


def get_password_from_secret(env_var):
    """Fetches the secret value from the docker secret file
    usually located inside /run/secrets/
    Arguments:
        env_var {str} -- Name of the environment variable
        containing the path to the secret file.
    Returns:
        [str] -- Secret value
    """
    passwd = None
    secret_file_path = os.environ.get(env_var)
    if secret_file_path:
        with open(secret_file_path) as secret_file:
            passwd = secret_file.read().strip()

    return passwd


def get_s3_config():
    check_s3_environment_variables()
    bucket = os.environ.get('BUCKET_NAME')

    conn = boto3.client(
        's3',
        region_name=os.environ.get('REGION'),
        aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('SECRET_ACCESS_KEY'),
        endpoint_url=os.environ.get('ENDPOINT_URL')
    )

    return conn, bucket


def upload_file_to_s3(filename, folder, conn, bucket):

    destpath = os.path.join(folder, os.path.basename(filename))
    try:
        print("Uploading file:", filename)
        conn.upload_file(filename, bucket, destpath)

    except Exception as e:
        print("Error uploading: %s" % (e))
        exit(1)


def list_directories(path):
    directories = []
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            directories.append(name)
    return directories


def get_site_config_from_path(site_config_path):
    site_config = dict()
    if os.path.exists(site_config_path):
        with open(site_config_path, 'r') as sc:
            site_config = json.load(sc)
    return site_config


def set_key_in_site_config(key, site, site_config_path):
    site_config = get_site_config_from_path(site_config_path)
    value = site_config.get(key)
    if value:
        print('Set {key} in site config for site: {site}'.format(key=key, site=site))
        update_site_config(key, value,
                            site_config_path=os.path.join(os.getcwd(), site, "site_config.json"))


def check_s3_environment_variables():
    if 'BUCKET_NAME' not in os.environ:
        print('Variable BUCKET_NAME not set')
        exit(1)

    if 'ACCESS_KEY_ID' not in os.environ:
        print('Variable ACCESS_KEY_ID not set')
        exit(1)

    if 'SECRET_ACCESS_KEY' not in os.environ:
        print('Variable SECRET_ACCESS_KEY not set')
        exit(1)

    if 'ENDPOINT_URL' not in os.environ:
        print('Variable ENDPOINT_URL not set')
        exit(1)

    if 'BUCKET_DIR' not in os.environ:
        print('Variable BUCKET_DIR not set')
        exit(1)

    if 'REGION' not in os.environ:
        print('Variable REGION not set')
        exit(1)
