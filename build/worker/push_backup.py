#!/home/frappe/frappe-bench/env/bin/python

import argparse
import os
import sys
from typing import List

import boto3
import frappe
from frappe.utils.backups import BackupGenerator


class Arguments(argparse.Namespace):
    site: str
    bucket: str
    region_name: str
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str


def get_bucket(arguments: Arguments):
    return boto3.resource(
        service_name="s3",
        endpoint_url=arguments.endpoint_url,
        region_name=arguments.region_name,
        aws_access_key_id=arguments.aws_access_key_id,
        aws_secret_access_key=arguments.aws_secret_access_key,
    ).Bucket(arguments.bucket)


def get_files(site_name: str):
    frappe.connect(site_name)
    backup_generator = BackupGenerator(
        db_name=frappe.conf.db_name,
        user=frappe.conf.db_name,
        password=frappe.conf.db_password,
        db_host=frappe.db.host,
        db_port=frappe.db.port,
        db_type=frappe.conf.db_type,
    )
    recent_backup_files = backup_generator.get_recent_backup(24)
    return [f for f in recent_backup_files if f]


def upload(arguments: Arguments):
    """Get latest backup files using Frappe utils, push them to S3 and remove local copy"""
    files = get_files(arguments.site)
    if not files:
        print("No backup found that was taken <24 hours ago.")
        return

    bucket = get_bucket(arguments)
    print(f"Uploading files: {str(files)}")

    for file_name in files:
        abs_file_path = os.path.abspath(file_name)
        bucket.upload_file(Filename=abs_file_path, Key=abs_file_path)
        os.remove(file_name)


def _parse_args(args: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--region-name", required=True)
    parser.add_argument("--endpoint-url", required=True)
    # Looking for default AWS credentials variables
    parser.add_argument(
        "--aws-access-key-id", required=True, default=os.getenv("AWS_ACCESS_KEY_ID")
    )
    parser.add_argument(
        "--aws-secret-access-key",
        required=True,
        default=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    return parser.parse_args(args, namespace=Arguments())


def main(args: List[str]) -> int:
    arguments = _parse_args(args)
    upload(arguments)
    return 0


if __name__ == "__main__":
    print(sys.argv[1:])
    raise SystemExit(main(sys.argv[1:]))
