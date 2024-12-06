import os
import subprocess
import pymysql
import time
from datetime import datetime
import boto3

mongo_host = "localhost"
mongo_user = "admin"
mongo_password = "chuashihong"
zip_password = "chuashihong"
log_db_host = "localhost"
log_db_user = "root"
log_db_password = "chuashihong"
s3_endpoint = "http://minio:9000"
s3_access_key = "chuashihong"
s3_secret_key = "chuashihong"
s3_bucket_name = "backups"

now = datetime.now()
timestamp = now.strftime("%Y-%m-%d_%H-%M")
backup_dir = r"C:\backup"
backup_file = os.path.join(backup_dir, f"mongo_backup_{timestamp}")
zip_file = f"{backup_file}.zip"

try:
    # Ensure the backup directory exists
    os.makedirs(backup_dir, exist_ok=True)

    # Perform the backup
    start_time = time.time()
    subprocess.run([
        "mongodump",
        "--host", mongo_host,
        "--port", "27017",
        "--authenticationDatabase", "admin",
        "-u", mongo_user,
        "-p", mongo_password,
        "--out", backup_file
    ], check=True)
    print(f"Backup file created: {backup_file}")

    # Zip the backup with a password using 7-Zip or zip command
    subprocess.run([
        "7z", "a", "-p" + zip_password, "-y", zip_file, backup_file
    ], check=True)  # Use "zip -P" instead if you use zip command
    print(f"Zipped backup file with password: {zip_file}")

    # Upload the zipped file to MinIO
    s3_client = boto3.client(
        's3',
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key
    )
    destination_folder = "mongo"
    s3_key = f"{destination_folder}/{timestamp}.zip"
    s3_client.upload_file(zip_file, s3_bucket_name, s3_key)
    print(f"Backup uploaded to MinIO: {s3_endpoint}/{s3_bucket_name}/{s3_key}")

    # Log backup completion
    connection = pymysql.connect(
        host=log_db_host,
        user=log_db_user,
        password=log_db_password,
        database="backup_log_db"
    )
    time_spent = time.time() - start_time
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO BackupRecord (instance_name, database_type, start_time, end_time, s3_uri, time_spent)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ("mongo-instance", "mongo", now, datetime.now(), f"{s3_endpoint}/{s3_bucket_name}/{s3_key}", time_spent))
    connection.commit()
    cursor.close()
    connection.close()
    print("Backup record logged successfully.")

except subprocess.CalledProcessError as e:
    print(f"Error during backup or zipping process: {e}")
except pymysql.MySQLError as e:
    print(f"Error logging to database: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
