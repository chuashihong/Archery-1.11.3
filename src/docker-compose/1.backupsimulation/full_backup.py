import os
import subprocess
import pymysql
import time
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


def perform_backup(mysql_host, mysql_user, mysql_password, backup_file):
    """
    Perform MySQL database backup using mysqldump.
    """
    try:
        subprocess.run([
            "mysqldump",
            "-h", mysql_host,
            "-u", mysql_user,
            f"--password={mysql_password}",
            "--all-databases",
            "--single-transaction",
            f"--result-file={backup_file}"
        ], check=True)
        print(f"Backup file created: {backup_file}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during backup process: {e}")


def zip_backup(backup_file, zip_file, zip_password):
    """
    Zip the backup file with a password.
    """
    try:
        subprocess.run(["zip", "-P", zip_password, zip_file, backup_file], check=True)
        print(f"Zipped backup file: {zip_file}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during zipping process: {e}")


def upload_to_minio(s3_endpoint, s3_access_key, s3_secret_key, s3_bucket_name, zip_file, s3_key):
    """
    Upload the zipped backup file to MinIO (S3).
    """
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key
        )
        s3_client.upload_file(zip_file, s3_bucket_name, s3_key)
        print(f"Backup uploaded to MinIO: {s3_endpoint}/{s3_bucket_name}/{s3_key}")
        return f"{s3_endpoint}/{s3_bucket_name}/{s3_key}"
    except (NoCredentialsError, PartialCredentialsError) as e:
        raise RuntimeError(f"Error with MinIO credentials: {e}")


def log_backup_to_db(log_db_host, log_db_user, log_db_password, s3_uri, start_time, end_time, time_spent):
    """
    Log backup completion details to the database.
    """
    try:
        connection = pymysql.connect(
            host=log_db_host,
            user=log_db_user,
            password=log_db_password,
            database="backup_log_db"
        )
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO BackupRecord (instance_name, database_type, start_time, end_time, s3_uri, time_spent)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("mysql-instance", "MySQL", start_time, end_time, s3_uri, time_spent))
        connection.commit()
        cursor.close()
        connection.close()
        print("Backup record logged successfully.")
    except pymysql.MySQLError as e:
        raise RuntimeError(f"Error logging to database: {e}")


def calculate_interval_times(interval_minutes=60):
    """
    Calculate start_time and end_time based on the current UTC time and a given interval in minutes.

    Args:
        interval_minutes (int): The interval in minutes for the time range. Defaults to 60 (hourly).

    Returns:
        tuple: (start_time, end_time) as UNIX timestamps (in seconds).
    """
    now = datetime.utcnow()

    # Calculate the base time for the interval
    zero = now - timedelta(
        minutes=now.minute % interval_minutes, 
        seconds=now.second, 
        microseconds=now.microsecond
    )

    # Calculate start and end times for the interval
    start_time = zero
    end_time = start_time + timedelta(minutes=interval_minutes)

    # Convert to UNIX timestamps (optional, for compatibility)
    start_timestamp = int(time.mktime(start_time.timetuple()))
    end_timestamp = int(time.mktime(end_time.timetuple()))

    return start_timestamp, end_timestamp

def calculate_interval_times(interval_minutes=60):
    """
    Calculate start_time and end_time based on the current UTC time and a given interval in minutes.

    Args:
        interval_minutes (int): The interval in minutes for the time range. Defaults to 60 (hourly).

    Returns:
        tuple: (start_time, end_time) as datetime objects.
    """
    now = datetime.utcnow()

    # Calculate the base time for the interval
    zero = now - timedelta(
        minutes=now.minute % interval_minutes, 
        seconds=now.second, 
        microseconds=now.microsecond
    )

    # Calculate start and end times for the interval
    start_time = zero
    end_time = start_time + timedelta(minutes=interval_minutes)

    return start_time, end_time

def main():
    # Load environment variables
    mysql_host = os.getenv("MYSQL_HOST")
    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    zip_password = os.getenv("ZIP_PASSWORD")
    log_db_host = os.getenv("BACKUP_LOG_DB_HOST")
    log_db_user = os.getenv("BACKUP_LOG_DB_USER")
    log_db_password = os.getenv("BACKUP_LOG_DB_PASSWORD")
    s3_endpoint = os.getenv("S3_ENDPOINT")
    s3_access_key = os.getenv("S3_ACCESS_KEY")
    s3_secret_key = os.getenv("S3_SECRET_KEY")
    s3_bucket_name = os.getenv("S3_BUCKET_NAME", "backups")

    # Backup timestamp
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    backup_file = f"/backup/mysql_backup_{timestamp}.sql"
    zip_file = f"{backup_file}.zip"
    destination_folder = "mysql"
    s3_key = f"{destination_folder}/{timestamp}.zip"

    try:
        # Get start_time and end_time as datetime objects
        start_time, end_time = calculate_interval_times(interval_minutes=10)

        # Perform backup (assuming perform_backup uses filenames or timestamps appropriately)
        perform_backup(mysql_host, mysql_user, mysql_password, backup_file)

        # Zip the backup file
        zip_backup(backup_file, zip_file, zip_password)

        # Upload to MinIO
        s3_uri = upload_to_minio(s3_endpoint, s3_access_key, s3_secret_key, s3_bucket_name, zip_file, s3_key)

        # Calculate total time spent in seconds
        total_time_spent = (datetime.utcnow() - start_time).total_seconds()

        # Log backup to the database
        log_backup_to_db(
            log_db_host, 
            log_db_user, 
            log_db_password, 
            s3_uri, 
            start_time.isoformat(),  # Use ISO format for readability
            end_time.isoformat(), 
            total_time_spent
        )


    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    main()
