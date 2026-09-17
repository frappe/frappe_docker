import os
import time

import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)


def main() -> int:
    endpoint_url = os.environ["S3_ENDPOINT_URL"]
    bucket = os.environ["S3_BUCKET"]
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name="us-east-1",
        config=Config(
            connect_timeout=2,
            read_timeout=2,
            retries={"max_attempts": 0},
            s3={"addressing_style": "path"},
        ),
    )
    deadline = time.monotonic() + 60
    while True:
        try:
            # Check credentials and bucket readiness from the backup client's network.
            client.head_bucket(Bucket=bucket)
            return 0
        except ClientError as exc:
            status = exc.response["ResponseMetadata"]["HTTPStatusCode"]
            if status != 404 and status < 500:
                raise
            error = exc
        except (
            ConnectionClosedError,
            ConnectTimeoutError,
            EndpointConnectionError,
            ReadTimeoutError,
        ) as exc:
            error = exc
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"S3 bucket {bucket!r} at {endpoint_url} was not ready within 60 seconds"
            ) from error
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
