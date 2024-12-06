import os
import subprocess
import pymysql
import time
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Load environment variables
mongo_host = "localhost"
mongo_user = "admin"
mongo_password = "chuashihong"
zip_password = "chuashihong"
log_db_host = "localhost"
log_db_user = "3308"
log_db_password = "chuashihong"
s3_endpoint = "http://minio:9000"  # MinIO server endpoint (e.g., http://minio:9000)
s3_access_key = "chuashihong"
s3_secret_key = "chuashihong"
s3_bucket_name = "backups"  # Default bucket name

# Backup timestamp

now = datetime.now()
timestamp = now.strftime("%Y-%m-%d_%H-%M")
backup_file = f".\\backup\\mongo_backup_{timestamp}"
# backup_file = r"C:\backup\mongo_backup_{timestamp}"
zip_file = f"{backup_file}.zip"

try:
    # Perform the backup
    start_time = time.time()
    subprocess.run([
        "mongodump",
        "--host", mongo_host,
        "--port", "27017",
        "--authenticationDatabase", mongo_user,
        "-u", mongo_user,
        "-p", mongo_password,
        "--out", backup_file

    ], check=True)
    print(f"Backup file created: {backup_file}")
  
    # Zip the backup with a password
    subprocess.run(["zip", "-P", zip_password, zip_file, backup_file], check=True)
    print(f"Zipped backup file: {zip_file}")

    # Initialize MinIO (S3) client
    s3_client = boto3.client(
        's3',
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_access_key, ##username
        aws_secret_access_key=s3_secret_key ##password
    )

    # Upload the zipped file to MinIO
    destination_folder = "mongo"  # Use the correct folder
    s3_key = f"{destination_folder}/{timestamp}.zip"
    s3_client.upload_file(zip_file, s3_bucket_name, s3_key)
    print(f"Backup uploaded to MinIO: {s3_endpoint}/{s3_bucket_name}/{s3_key}")

    # Log backup completion
    end_time = time.time()
    connection = pymysql.connect(
        host=log_db_host,
        user=log_db_user,
        password=log_db_password,
        database="backup_log_db"  # Use the correct database
    )
    time_spent = end_time - start_time

    filename_time = now.replace(second=0, microsecond=0) - timedelta(minutes=1)  # 1 minute before current time
    backup_start_time = filename_time.replace(second=0)  # Start of the minute
    backup_end_time = filename_time.replace(second=59)  # End of the minute

    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO BackupRecord (instance_name, database_type, start_time, end_time, s3_uri, time_spent)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ("mongo-instance", "mongo", backup_start_time, backup_end_time, f"{s3_endpoint}/{s3_bucket_name}/{s3_key}", time_spent))
    connection.commit()
    cursor.close()
    connection.close()
    print("Backup record logged successfully.")

except subprocess.CalledProcessError as e:
    print(f"Error during backup process: {e}")
except (NoCredentialsError, PartialCredentialsError) as e:
    print(f"Error with MinIO credentials: {e}")
except pymysql.MySQLError as e:
    print(f"Error logging to database: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
