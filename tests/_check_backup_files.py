import os

import boto3


def main() -> int:
    resource = boto3.resource(
        service_name="s3",
        endpoint_url="http://minio:9000",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    )
    bucket = resource.Bucket("frappe")
    db = False
    config = False
    private_files = False
    public_files = False
    for obj in bucket.objects.all():
        if obj.key.endswith("database.sql.gz"):
            db = True
        elif obj.key.endswith("site_config_backup.json"):
            config = True
        elif obj.key.endswith("private-files.tar"):
            private_files = True
        elif obj.key.endswith("files.tar"):
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
    print("All files was pushed to S3!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
