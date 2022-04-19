#!/home/frappe/frappe-bench/env/bin/python
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, cast

import boto3
import frappe
from frappe.utils.backups import BackupGenerator

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import _Bucket


class Arguments(argparse.Namespace):
    site: str
    bucket: str
    region_name: str
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    bucket_directory: str


def _get_files_from_previous_backup(site_name: str) -> list[Path]:
    frappe.connect(site_name)

    conf = cast(Any, frappe.conf)
    backup_generator = BackupGenerator(
        db_name=conf.db_name,
        user=conf.db_name,
        password=conf.db_password,
        db_host=frappe.db.host,
        db_port=frappe.db.port,
        db_type=conf.db_type,
    )
    recent_backup_files = backup_generator.get_recent_backup(24)

    frappe.destroy()
    return [Path(f) for f in recent_backup_files if f]


def get_files_from_previous_backup(site_name: str) -> list[Path]:
    files = _get_files_from_previous_backup(site_name)
    if not files:
        print("No backup found that was taken <24 hours ago.")
    return files


def get_bucket(args: Arguments) -> _Bucket:
    return boto3.resource(
        service_name="s3",
        endpoint_url=args.endpoint_url,
        region_name=args.region_name,
        aws_access_key_id=args.aws_access_key_id,
        aws_secret_access_key=args.aws_secret_access_key,
    ).Bucket(args.bucket)


def upload_file(
    path: Path, site_name: str, bucket: _Bucket, bucket_directory: str = None
) -> None:
    filename = str(path.absolute())
    key = str(Path(site_name) / path.name)
    if bucket_directory:
        key = bucket_directory + "/" + key
    print(f"Uploading {key}")
    bucket.upload_file(Filename=filename, Key=key)
    os.remove(path)


def push_backup(args: Arguments) -> None:
    """Get latest backup files using Frappe utils, push them to S3 and remove local copy"""

    files = get_files_from_previous_backup(args.site)
    bucket = get_bucket(args)

    for path in files:
        upload_file(
            path=path,
            site_name=args.site,
            bucket=bucket,
            bucket_directory=args.bucket_directory,
        )

    print("Done!")


def parse_args(args: list[str]) -> Arguments:
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
    parser.add_argument("--bucket-directory")
    return parser.parse_args(args, namespace=Arguments())


def main(args: list[str]) -> int:
    push_backup(parse_args(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
