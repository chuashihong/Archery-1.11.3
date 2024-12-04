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
restore_database = f"{database}_{timestamp}"

# Parse S3 bucket and object key from URI
bucket_name, object_key = s3_uri.split("/", 3)[-1].split("/", 1)

# Download backup file from MinIO
print("Connecting to S3...")
local_zip_path = f"/tmp/{object_key.split('/')[-1]}"
s3_client = boto3.client(
    's3',
    aws_access_key_id=key,
    aws_secret_access_key=secret,
    endpoint_url='http://host.docker.internal:9000'
)
print("Connected")
print("bucket_name, object key and local_zip_path", bucket_name, object_key, local_zip_path)
s3_client.download_file(bucket_name, object_key, local_zip_path)
print(f"Downloaded {s3_uri} to {local_zip_path}")

# Unzip the backup file to /tmp/backup/
extraction_dir = "/tmp/backup"
os.makedirs(extraction_dir, exist_ok=True)  # Ensure the extraction directory exists
subprocess.run(
    ["unzip", "-P", zip_password, "-j", local_zip_path, "-d", extraction_dir],
    check=True
)
print(f"Unzipped to {extraction_dir}")

# Rename the original database to `db1_temp`
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    cursor.execute(f"RENAME DATABASE `{database}` TO `{database}_temp`")
    print(f"Renamed `{database}` to `{database}_temp`")
connection.commit()
connection.close()

# Create a new database `db1`
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    cursor.execute(f"CREATE DATABASE `{database}`")
    print(f"Created new database `{database}` for restore")
connection.commit()
connection.close()

# Restore the backup to the new `db1`
backup_file = os.path.join(extraction_dir, "mysql_backup_2024-12-04_07-50.sql")
restore_command = [
    "mysql",
    "-h", host,
    "-P", port,
    "-u", user,
    f"--password={password}",
    database
]
with open(backup_file, "r") as sql_file:
    subprocess.run(restore_command, stdin=sql_file, check=True)
print(f"Restored backup to `{database}`")

# Rename the restored `db1` to `db1_{timestamp}`
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    cursor.execute(f"RENAME DATABASE `{database}` TO `{restore_database}`")
    print(f"Renamed `{database}` to `{restore_database}`")
connection.commit()
connection.close()

# Rename `db1_temp` back to `db1`
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    cursor.execute(f"RENAME DATABASE `{database}_temp` TO `{database}`")
    print(f"Renamed `{database}_temp` back to `{database}`")
connection.commit()
connection.close()

# Rename the table in the restored database
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password,
    database=restore_database
)
with connection.cursor() as cursor:
    restored_table_name = f"{table}_restore_{timestamp}"
    cursor.execute(f"RENAME TABLE `{table}` TO `{restored_table_name}`")
    print(f"Renamed table `{table}` to `{restored_table_name}` in `{restore_database}`")
connection.commit()
connection.close()
