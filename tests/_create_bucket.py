import os
import time
import sys

def main() -> int:
    # Import boto3 with error handling
    try:
        import boto3
        from botocore.exceptions import ClientError, EndpointConnectionError
    except ImportError as e:
        print(f"ERROR: boto3 not available: {e}", file=sys.stderr)
        return 1
    
    # Get environment variables
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    
    if not access_key or not secret_key:
        print("ERROR: S3_ACCESS_KEY or S3_SECRET_KEY not set", file=sys.stderr)
        return 1
    
    print(f"Connecting to MinIO with access key: {access_key[:10]}...")
    
    # Create S3 resource with retry logic
    for attempt in range(10):  # Try up to 10 times
        try:
            resource = boto3.resource(
                service_name="s3",
                endpoint_url="http://minio:9000",
                region_name="us-east-1",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            
            # Test connection by listing buckets
            list(resource.buckets.all())
            print("Connected to MinIO successfully")
            break
            
        except EndpointConnectionError:
            print(f"Attempt {attempt + 1}: MinIO not ready yet, waiting...")
            time.sleep(2)
        except Exception as e:
            print(f"Attempt {attempt + 1}: Connection failed: {e}")
            if attempt == 9:  # Last attempt
                print("Failed to connect to MinIO after 10 attempts", file=sys.stderr)
                return 1
            time.sleep(2)
    
    # Create bucket
    try:
        resource.create_bucket(Bucket="frappe")
        print("Bucket 'frappe' created successfully")
        return 0
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            print("Bucket 'frappe' already exists")
            return 0
        else:
            print(f"ERROR creating bucket: {e}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"ERROR creating bucket: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())