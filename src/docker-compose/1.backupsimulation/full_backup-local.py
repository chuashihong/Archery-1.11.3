import os
import subprocess
import pymysql
import time
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Load environment variables
mysql_host = "127.0.0.1"
mysql_user = "root"
mysql_password = "chuashihong"
zip_password = "chuashihong"
log_db_host = "127.0.0.1"
log_db_user = "root"
log_db_password = "chuashihong"
s3_endpoint = "http://minio:9000"  # MinIO server endpoint (e.g., http://minio:9000)
s3_access_key = "chuashihong"
s3_secret_key = "chuashihong"
s3_bucket_name = os.getenv("S3_BUCKET_NAME", "backups")  # Default bucket name

# Backup timestamp

now = datetime.now()
timestamp = now.strftime("%Y-%m-%d_%H-%M")
# backup_file = f"./backup/mysql_backup_{timestamp}.sql"
backup_dir = "./backup"
backup_file = os.path.join(backup_dir, f"mysql_backup_{timestamp}.sql")
zip_file = f"{backup_file}.zip"

try:
    # Perform the backup
    start_time = time.time()
    subprocess.run([
        "mysqldump",
        "-h", mysql_host,
        "-P", "3309",
        "-u", mysql_user,
        f"--password={mysql_password}",
        "--all-databases",
        "--single-transaction",
        f"--result-file={backup_file}"
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
    destination_folder = "mysql"  # Use the correct folder
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
    """, ("mysql-instance", "MySQL", backup_start_time, backup_end_time, f"{s3_endpoint}/{s3_bucket_name}/{s3_key}", time_spent))
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
