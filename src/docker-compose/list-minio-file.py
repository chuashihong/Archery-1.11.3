import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Load MinIO/S3 connection details from environment variables
s3_endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")  # Replace with your MinIO endpoint
s3_access_key = os.getenv("S3_ACCESS_KEY", "chuashihong")  # Replace with your S3 access key
s3_secret_key = os.getenv("S3_SECRET_KEY", "chuashihong")  # Replace with your S3 secret key
s3_bucket_name = os.getenv("S3_BUCKET_NAME", "backups")  # Replace with your bucket name

def list_files_in_bucket():
    try:
        # Initialize MinIO (S3) client
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key
        )
        
        # List files in the specified bucket
        response = s3_client.list_objects_v2(Bucket=s3_bucket_name)
        if 'Contents' in response:
            print(f"Files in bucket '{s3_bucket_name}':")
            for obj in response['Contents']:
                print(f"- {obj['Key']} (Last modified: {obj['LastModified']}, Size: {obj['Size']} bytes)")
        else:
            print(f"No files found in bucket '{s3_bucket_name}'.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error with credentials: {e}")
    except ClientError as e:
        print(f"Client error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    list_files_in_bucket()
