import os
import time
import boto3

import datetime
from glob import glob
from frappe.utils import get_sites

def get_file_ext():
    return {
        "database": "-database.sql.gz",
        "private_files": "-private-files.tar",
        "public_files": "-files.tar"
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

def get_s3_config():
    check_environment_variables()
    bucket = os.environ.get('BUCKET_NAME')

    conn = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('SECRET_ACCESS_KEY'),
        endpoint_url=os.environ.get('ENDPOINT_URL')
    )

    return conn, bucket

def check_environment_variables():
    if not 'BUCKET_NAME' in os.environ:
        print('Variable BUCKET_NAME not set')
        exit(1)

    if not 'ACCESS_KEY_ID' in os.environ:
        print('Variable ACCESS_KEY_ID not set')
        exit(1)

    if not 'SECRET_ACCESS_KEY' in os.environ:
        print('Variable SECRET_ACCESS_KEY not set')
        exit(1)

    if not 'ENDPOINT_URL' in os.environ:
        print('Variable ENDPOINT_URL not set')
        exit(1)

    if not 'BUCKET_DIR' in os.environ:
        print('Variable BUCKET_DIR not set')
        exit(1)

def upload_file_to_s3(filename, folder, conn, bucket):

    destpath = os.path.join(folder, os.path.basename(filename))
    try:
        print("Uploading file:", filename)
        conn.upload_file(filename, bucket, destpath)

    except Exception as e:
        print("Error uploading: %s" % (e))
        exit(1)

def delete_old_backups(limit, bucket, folder):
    all_backups = list()
    backup_limit = int(limit)
    check_environment_variables()
    bucket_dir = os.environ.get('BUCKET_DIR')

    s3 = boto3.resource(
        's3',
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
            if obj.get('Prefix') in folder:
                for backup_obj in bucket.objects.filter(Prefix=obj.get('Prefix')):
                    try:
                        backup_dir = backup_obj.key.split('/')[1]
                        all_backups.append(backup_dir)
                    except expression as error:
                        print(error)
                        exit(1)

    all_backups = set(sorted(all_backups))
    if len(all_backups) > backup_limit:
        latest_backup = sorted(all_backups)[0] if len(all_backups) > 0 else None
        print("Deleting Backup: {0}".format(latest_backup))
        for obj in bucket.objects.filter(Prefix=bucket_dir + '/' + latest_backup):
            # delete all keys that are inside the latest_backup
            if bucket_dir in obj.key:
                try:
                    delete_directory = obj.key.split('/')[1]
                    print('Deleteing ' + obj.key)
                    s3.Object(bucket.name, obj.key).delete()
                except expression as error:
                    print(error)
                    exit(1)

def main():
    details = dict()
    sites = get_sites()
    conn, bucket = get_s3_config()

    for site in sites:
        details = get_backup_details(site)
        db_file = details.get('database', {}).get('file_path')
        folder = None
        if db_file:
            folder = os.environ.get('BUCKET_DIR') + '/' + os.path.basename(db_file)[:15] + '/'
            upload_file_to_s3(db_file, folder, conn, bucket)

        public_files = details.get('public_files', {}).get('file_path')
        if public_files:
            folder = os.environ.get('BUCKET_DIR') + '/' + os.path.basename(public_files)[:15] + '/'
            upload_file_to_s3(public_files, folder, conn, bucket)

        private_files = details.get('private_files', {}).get('file_path')
        if private_files:
            folder = os.environ.get('BUCKET_DIR') + '/' + os.path.basename(private_files)[:15] + '/'
            upload_file_to_s3(private_files, folder, conn, bucket)

        if folder:
            delete_old_backups(os.environ.get('BACKUP_LIMIT', '3'), bucket, folder)

    print('push-backup complete')
    exit(0)

if __name__ == "__main__":
    main()
