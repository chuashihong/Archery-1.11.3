import os
import subprocess
import pymysql
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Load environment variables
# mysql_host = os.getenv("MYSQL_HOST")
# mysql_user = os.getenv("MYSQL_USER")
# mysql_password = os.getenv("MYSQL_PASSWORD")
# log_db_host = os.getenv("BACKUP_LOG_DB_HOST")
# log_db_user = os.getenv("BACKUP_LOG_DB_USER")
# log_db_password = os.getenv("BACKUP_LOG_DB_PASSWORD")
# binlog_dir = "/backup/binlogs"  # Directory to store binary logs
# zip_password = os.getenv("ZIP_PASSWORD")
# s3_endpoint = os.getenv("S3_ENDPOINT")
# s3_access_key = os.getenv("S3_ACCESS_KEY")
# s3_secret_key = os.getenv("S3_SECRET_KEY")
# s3_bucket_name = os.getenv("S3_BUCKET_NAME", "backups")
mysql_host = "localhost"
mysql_user = "root"
mysql_port = 3309
mysql_password = "chuashihong"
log_db_host = "localhost"
log_db_port = 3308
log_db_user = "root"
log_db_password = "chuashihong"
binlog_dir = "/backup/binlogs"  # Directory to store binary logs
zip_password = "chuashihong"
s3_endpoint = "http://minio:9000"
s3_access_key = "chuashihong"
s3_secret_key = "chuashihong"
s3_bucket_name = os.getenv("S3_BUCKET_NAME", "backups")
destination_folder = "mysql-inc"  # S3 destination folder for incremental backups

# Ensure backup directory exists
os.makedirs(binlog_dir, exist_ok=True)

def get_binlog_files():
    """Retrieve the list of binary log files from MySQL."""
    try:
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password
        )
        cursor = connection.cursor()
        cursor.execute("SHOW BINARY LOGS;")
        binlogs = cursor.fetchall()
        cursor.close()
        connection.close()
        return [row[0] for row in binlogs]
    except pymysql.MySQLError as e:
        print(f"Error retrieving binary log files: {e}")
        return []

def log_backup_to_db(start_time, end_time, s3_uri):
    """Logs the backup details to the logging database."""
    try:
        connection = pymysql.connect(
            host=log_db_host,
            user=log_db_user,
            port=log_db_port,
            password=log_db_password,
            database="backup_log_db"  # Use your actual logging DB name
        )
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO IncBackupRecord (instance_name, database_type, start_time, end_time, s3_uri)
            VALUES (%s, %s, %s, %s, %s)
        """, ("mysql-instance", "MySQL", start_time, end_time, s3_uri))
        connection.commit()
        cursor.close()
        connection.close()
        print("Backup record logged successfully.")
    except pymysql.MySQLError as e:
        print(f"Error logging to database: {e}")

def perform_incremental_backup():
    """Performs incremental backup within the last hour using mysqlbinlog."""
    try:
        # Time range for the last hour
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=1)
        start_datetime = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_datetime = end_time.strftime("%Y-%m-%d %H:%M:%S")

        # Generate a timestamped backup file
        timestamp = end_time.strftime("%Y-%m-%d_%H-%M")
        backup_file = f"{binlog_dir}/binlog_backup_{timestamp}.sql"
        zip_file = f"{backup_file}.zip"

        # Get the binary log files
        binlog_files = get_binlog_files()
        if not binlog_files:
            print("No binary log files found.")
            return

        print(f"Binlog Files:", binlog_files)
        # Use mysqlbinlog to fetch logs within the time range
        for binlog_file in binlog_files:
            subprocess.run([
                "mysqlbinlog",
                "--read-from-remote-server",
                "--host", mysql_host,
                "--port", str(mysql_port),
                "--user", mysql_user,
                f"--password={mysql_password}",
                "--start-datetime", start_datetime,
                "--stop-datetime", end_datetime,
                binlog_file,
                "--result-file", backup_file
            ], check=True)
            print(f"Incremental backup file created: {backup_file}")

        # Zip the backup with a password
        subprocess.run(["zip", "-P", zip_password, zip_file, backup_file], check=True)
        print(f"Zipped incremental backup file: {zip_file}")

        # Upload the zipped file to S3/MinIO
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key
        )
        s3_key = f"{destination_folder}/{os.path.basename(zip_file)}"
        s3_client.upload_file(zip_file, s3_bucket_name, s3_key)
        print(f"Incremental backup uploaded to MinIO: {s3_endpoint}/{s3_bucket_name}/{s3_key}")

        # Log backup completion to the database
        log_backup_to_db(
            start_time=start_time,
            end_time=end_time,
            s3_uri=f"{s3_endpoint}/{s3_bucket_name}/{s3_key}"
        )

    except subprocess.CalledProcessError as e:
        print(f"Error during incremental backup process: {e}")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error with MinIO credentials: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    perform_incremental_backup()
