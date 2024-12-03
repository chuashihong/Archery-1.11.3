import os
import subprocess
import pymysql
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from datetime import datetime

# Load environment variables
log_db_host = os.getenv("BACKUP_LOG_DB_HOST")
log_db_user = os.getenv("BACKUP_LOG_DB_USER")
log_db_password = os.getenv("BACKUP_LOG_DB_PASSWORD")
restore_db_host = os.getenv("RESTORE_DB_HOST")
restore_db_user = os.getenv("RESTORE_DB_USER")
restore_db_password = os.getenv("RESTORE_DB_PASSWORD")
s3_endpoint = os.getenv("S3_ENDPOINT")
s3_access_key = os.getenv("S3_ACCESS_KEY")
s3_secret_key = os.getenv("S3_SECRET_KEY")
s3_bucket_name = os.getenv("S3_BUCKET_NAME", "backups")
zip_password = os.getenv("ZIP_PASSWORD")

def get_latest_backup_uri():
    """Fetch the S3 URI of the latest backup from the log database."""
    try:
        connection = pymysql.connect(
            host=log_db_host,
            user=log_db_user,
            password=log_db_password,
            database="backup_log_db"
        )
        cursor = connection.cursor()
        cursor.execute("""
            SELECT s3_uri FROM BackupRecord
            ORDER BY end_time DESC LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            raise Exception("No backup records found in the database.")
    finally:
        cursor.close()
        connection.close()

def download_backup(s3_uri, local_path):
    """Download a backup file from MinIO."""
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key
        )
        bucket_name, s3_key = s3_uri.split('/', 3)[-1].split('/', 1)
        s3_client.download_file(bucket_name, s3_key, local_path)
        print(f"Downloaded {s3_uri} to {local_path}")
    except NoCredentialsError:
        raise Exception("MinIO credentials are missing.")
    except Exception as e:
        raise Exception(f"Error downloading backup: {e}")

def unzip_backup(zip_file, output_file):
    """Unzip the backup file using the provided password."""
    try:
        subprocess.run(["unzip", "-P", zip_password, "-o", zip_file, "-d", "/restore"], check=True)
        print(f"Unzipped backup file: {output_file}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error unzipping backup: {e}")

def restore_backup_to_database(sql_file):
    """Restore the unzipped SQL file to the database."""
    try:
        subprocess.run([
            "mysql",
            "-h", restore_db_host,
            "-u", restore_db_user,
            f"--password={restore_db_password}",
            "<", sql_file
        ], check=True)
        print(f"Restored backup from {sql_file} to database {restore_db_host}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error restoring database: {e}")

def main():
    try:
        print("Starting restore workflow...")
        # Step 1: Get the S3 URI of the latest backup
        latest_backup_uri = get_latest_backup_uri()
        print(f"Latest backup URI: {latest_backup_uri}")

        # Step 2: Download the backup file from MinIO
        local_zip_file = "/restore/latest_backup.zip"
        download_backup(latest_backup_uri, local_zip_file)

        # Step 3: Unzip the backup file
        local_sql_file = "/restore/latest_backup.sql"
        unzip_backup(local_zip_file, local_sql_file)

        # Step 4: Restore the database from the SQL file
        restore_backup_to_database(local_sql_file)

        print("Restore workflow completed successfully.")
    except Exception as e:
        print(f"An error occurred during the restore workflow: {e}")

if __name__ == "__main__":
    main()
