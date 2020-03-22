import os
import json
import semantic_version
import git

from migrate import migrate_sites
from check_connection import get_config

APP_VERSIONS_JSON_FILE = 'app_versions.json'
APPS_TXT_FILE = 'apps.txt'

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
    except:
        print(APPS_TXT_FILE+" is not valid")
        exit(1)

    return apps

def get_container_versions(apps):
    versions = {}
    for app in apps:
        try:
            version = __import__(app).__version__
            versions.update({app:version})
        except:
            pass

        try:
            path = os.path.join('..','apps', app)
            repo = git.Repo(path)
            commit_hash = repo.head.object.hexsha
            versions.update({app+'_git_hash':commit_hash})
        except:
            pass

    return versions

def get_version_file():
    versions = None
    try:
        with open(APP_VERSIONS_JSON_FILE) as versions_file:
            versions = json.load(versions_file)
    except:
        pass
    return versions

def main():
    is_ready = False
    apps = get_apps()

    container_versions = get_container_versions(apps)

    version_file = get_version_file()

    if not version_file:
        version_file = container_versions
        save_version_file(version_file)

    for app in apps:
        container_version = None
        file_version = None
        version_file_hash = None
        container_hash = None

        repo = git.Repo(os.path.join('..','apps',app))
        branch = repo.active_branch.name

        if branch == 'develop':
            version_file_hash = version_file.get(app+'_git_hash')
            container_hash = container_versions.get(app+'_git_hash')
            if container_hash and version_file_hash:
                if container_hash != version_file_hash:
                    is_ready = True
                    break

        if version_file.get(app):
            file_version = semantic_version.Version(version_file.get(app))

        if container_versions.get(app):
            container_version = semantic_version.Version(container_versions.get(app))

        if file_version and container_version:
            if container_version > file_version:
                is_ready = True
                break

    config = get_config()

    if is_ready and config.get('maintenance_mode') != 1:
        migrate_sites(maintenance_mode=True)
        version_file = container_versions
        save_version_file(version_file)

if __name__ == "__main__":
    main()
