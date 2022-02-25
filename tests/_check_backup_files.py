import os
import re
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import BucketObjectsCollection, _Bucket


def get_bucket() -> "_Bucket":
    return boto3.resource(
        service_name="s3",
        endpoint_url="http://minio:9000",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    ).Bucket("frappe")


def get_key_builder():
    site_name = os.getenv("SITE_NAME")
    assert site_name

    def builder(key: str, suffix: str) -> bool:
        return bool(re.match(rf"{site_name}.*{suffix}$", key))

    return builder


def check_keys(objects: "BucketObjectsCollection"):
    check_key = get_key_builder()

    db = False
    config = False
    private_files = False
    public_files = False

    for obj in objects:
        if check_key(obj.key, "database.sql.gz"):
            db = True
        elif check_key(obj.key, "site_config_backup.json"):
            config = True
        elif check_key(obj.key, "private-files.tar"):
            private_files = True
        elif check_key(obj.key, "files.tar"):
            public_files = True

    exc = lambda type_: Exception(f"Didn't push {type_} backup")
    if not db:
        raise exc("database")
    if not config:
        raise exc("site config")
    if not private_files:
        raise exc("private files")
    if not public_files:
        raise exc("public files")

    print("All files were pushed to S3!")


def main() -> int:
    bucket = get_bucket()
    check_keys(bucket.objects.all())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
