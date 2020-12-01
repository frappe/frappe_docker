import os
import semantic_version
import git

from migrate import migrate_sites
from utils import (
    save_version_file,
    get_apps,
    get_container_versions,
    get_version_file,
    get_config
)


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

        repo = git.Repo(os.path.join('..', 'apps', app))
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
