from datetime import datetime
import subprocess
import boto3
import pymysql
import os

# Retrieve data from AJAX request
instance = "mysql-instance"
database = "db1"
table = "table1"
s3_uri = "http://minio:9000/backups/mysql/2024-12-04_07-50.zip"
region = ""
key = "chuashihong"
secret = "chuashihong"
host = "host.docker.internal"
port = "3309"
user = "root"
password = "chuashihong"
zip_password = "chuashihong"

# Generate a timestamped database name
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
restore_database = f"{database}_restore_{timestamp}"

# Parse S3 bucket and object key from URI
bucket_name, object_key = s3_uri.split("/", 3)[-1].split("/", 1)

# Download backup file from MinIO
print("connecting to s3")
local_zip_path = f"/tmp/{object_key.split('/')[-1]}"
s3_client = boto3.client(
    's3',
    aws_access_key_id=key,
    aws_secret_access_key=secret,
    endpoint_url='http://host.docker.internal:9000'
)
print("connected")
print("bucket_name, object key and local_zip_path", bucket_name, object_key, local_zip_path)
s3_client.download_file(bucket_name, object_key, local_zip_path)
print(f"Downloaded {s3_uri} to {local_zip_path}")

# Unzip the backup file to /tmp/backup/
extraction_dir = "/tmp/backup"
os.makedirs(extraction_dir, exist_ok=True)  # Ensure the extraction directory exists
# Unzip the backup file to /tmp/backup/ without creating subdirectories
subprocess.run(
    ["unzip", "-P", zip_password, "-j", local_zip_path, "-d", extraction_dir],
    check=True
)
print(f"Unzipped to {extraction_dir}")

# Construct the expected path for the SQL file
sql_file_name = "mysql_backup_2024-12-04_07-50.sql"
local_sql_path = os.path.join(extraction_dir, sql_file_name)
if not os.path.exists(local_sql_path):
    raise FileNotFoundError(f"Expected SQL file not found: {local_sql_path}")
print(f"SQL file located at: {local_sql_path}")


# Connect to MySQL to create the new restore database
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    # Create the restore database
    cursor.execute(f"CREATE DATABASE `{restore_database}`")
    print(f"Created restore database: `{restore_database}`")
connection.commit()
connection.close()

# Restore the table to the new database
restore_command = [
    "mysql",
    "-h", host,
    "-P", port,
    "-u", user,
    f"--password={password}",
    restore_database
]
with open(local_sql_path, "r") as sql_file:
    subprocess.run(restore_command, stdin=sql_file, check=True)
print(f"Restored {table} to {restore_database}")

# Rename the table in the restore database
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password,
    database=restore_database
)
with connection.cursor() as cursor:
    restored_table_name = f"{table}_restore_{timestamp}"
    cursor.execute(f"RENAME TABLE {table} TO {restored_table_name}")
    print(f"Renamed table {table} to {restored_table_name}")
connection.commit()
connection.close()
