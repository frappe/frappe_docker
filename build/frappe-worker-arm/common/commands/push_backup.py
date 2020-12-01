import os
import time
import boto3

import datetime
from glob import glob
from frappe.utils import get_sites
from constants import DATE_FORMAT
from utils import (
    get_s3_config,
    upload_file_to_s3,
    check_s3_environment_variables,
)


def get_file_ext():
    return {
        "database": "-database.sql.gz",
        "private_files": "-private-files.tar",
        "public_files": "-files.tar",
        "site_config": "-site_config_backup.json"
    }


def get_backup_details(sitename):
    backup_details = dict()
    file_ext = get_file_ext()

    # add trailing slash https://stackoverflow.com/a/15010678
    site_backup_path = os.path.join(os.getcwd(), sitename, "private", "backups", "")

    if os.path.exists(site_backup_path):
        for filetype, ext in file_ext.items():
            site_slug = sitename.replace('.', '_')
            pattern = site_backup_path + '*-' + site_slug + ext
            backup_files = list(filter(os.path.isfile, glob(pattern)))

            if len(backup_files) > 0:
                backup_files.sort(key=lambda file: os.stat(os.path.join(site_backup_path, file)).st_ctime)
                backup_date = datetime.datetime.strptime(time.ctime(os.path.getmtime(backup_files[0])), "%a %b %d %H:%M:%S %Y")
                backup_details[filetype] = {
                    "sitename": sitename,
                    "file_size_in_bytes": os.stat(backup_files[-1]).st_size,
                    "file_path": os.path.abspath(backup_files[-1]),
                    "filename": os.path.basename(backup_files[-1]),
                    "backup_date": backup_date.date().strftime("%Y-%m-%d %H:%M:%S")
                }

    return backup_details


def delete_old_backups(limit, bucket, site_name):
    all_backups = list()
    all_backup_dates = list()
    backup_limit = int(limit)
    check_s3_environment_variables()
    bucket_dir = os.environ.get('BUCKET_DIR')
    oldest_backup_date = None

    s3 = boto3.resource(
        's3',
        region_name=os.environ.get('REGION'),
        aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('SECRET_ACCESS_KEY'),
        endpoint_url=os.environ.get('ENDPOINT_URL')
    )

    bucket = s3.Bucket(bucket)
    objects = bucket.meta.client.list_objects_v2(
        Bucket=bucket.name,
        Delimiter='/')

    if objects:
        for obj in objects.get('CommonPrefixes'):
            if obj.get('Prefix') == bucket_dir + '/':
                for backup_obj in bucket.objects.filter(Prefix=obj.get('Prefix')):
                    if backup_obj.get()["ContentType"] == "application/x-directory":
                        continue
                    try:
                        # backup_obj.key is bucket_dir/site/date_time/backupfile.extension
                        bucket_dir, site_slug, date_time, backupfile = backup_obj.key.split('/')
                        date_time_object = datetime.datetime.strptime(
                            date_time, DATE_FORMAT
                        )

                        if site_name in backup_obj.key:
                            all_backup_dates.append(date_time_object)
                            all_backups.append(backup_obj.key)
                    except IndexError as error:
                        print(error)
                        exit(1)

    if len(all_backup_dates) > 0:
        oldest_backup_date = min(all_backup_dates)

    if len(all_backups) / 3 > backup_limit:
        oldest_backup = None
        for backup in all_backups:
            try:
                # backup is bucket_dir/site/date_time/backupfile.extension
                backup_dir, site_slug, backup_dt_string, filename = backup.split('/')
                backup_datetime = datetime.datetime.strptime(
                    backup_dt_string, DATE_FORMAT
                )
                if backup_datetime == oldest_backup_date:
                    oldest_backup = backup

            except IndexError as error:
                print(error)
                exit(1)

            if oldest_backup:
                for obj in bucket.objects.filter(Prefix=oldest_backup):
                    # delete all keys that are inside the oldest_backup
                    if bucket_dir in obj.key:
                        print('Deleteing ' + obj.key)
                        s3.Object(bucket.name, obj.key).delete()


def main():
    details = dict()
    sites = get_sites()
    conn, bucket = get_s3_config()

    for site in sites:
        details = get_backup_details(site)
        db_file = details.get('database', {}).get('file_path')
        folder = os.environ.get('BUCKET_DIR') + '/' + site + '/'
        if db_file:
            folder = os.environ.get('BUCKET_DIR') + '/' + site + '/' + os.path.basename(db_file)[:15] + '/'
            upload_file_to_s3(db_file, folder, conn, bucket)

            # Archive site_config.json
            site_config_file = details.get('site_config', {}).get('file_path')
            if not site_config_file:
                site_config_file = os.path.join(os.getcwd(), site, 'site_config.json')
            upload_file_to_s3(site_config_file, folder, conn, bucket)

        public_files = details.get('public_files', {}).get('file_path')
        if public_files:
            folder = os.environ.get('BUCKET_DIR') + '/' + site + '/' + os.path.basename(public_files)[:15] + '/'
            upload_file_to_s3(public_files, folder, conn, bucket)

        private_files = details.get('private_files', {}).get('file_path')
        if private_files:
            folder = os.environ.get('BUCKET_DIR') + '/' + site + '/' + os.path.basename(private_files)[:15] + '/'
            upload_file_to_s3(private_files, folder, conn, bucket)

        delete_old_backups(os.environ.get('BACKUP_LIMIT', '3'), bucket, site)

    print('push-backup complete')
    exit(0)


if __name__ == "__main__":
    main()
