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

# Step 1: Dump the original database `db1` to a SQL file
dump_file = f"/tmp/{database}_temp_dump_{timestamp}.sql"
dump_command = [
    "mysqldump",
    "-h", host,
    "-P", port,
    "-u", user,
    f"--password={password}",
    database
]
with open(dump_file, "w") as file:
    subprocess.run(dump_command, stdout=file, check=True)
print(f"Dumped `{database}` to `{dump_file}`")

# Step 2: Create a new database `db1_temp`
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    cursor.execute(f"CREATE DATABASE `{database}_temp`")
    print(f"Created new database `{database}_temp`")
connection.commit()
connection.close()

# Step 3: Restore the dump into the new database `db1_temp`
restore_command = [
    "mysql",
    "-h", host,
    "-P", port,
    "-u", user,
    f"--password={password}",
    f"{database}_temp"
]
with open(dump_file, "r") as file:
    subprocess.run(restore_command, stdin=file, check=True)
print(f"Restored `{dump_file}` into `{database}_temp`")

# Step 4: Drop the original database `db1`
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    cursor.execute(f"DROP DATABASE `{database}`")
    print(f"Dropped original database `{database}`")
connection.commit()
connection.close()

# Step 5: Create a new `db1` for the restore operation
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

# Step 6: Restore the backup to the new `db1`
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

# Step 7: Rename the restored `db1` to `db1_{timestamp}`
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    cursor.execute(f"CREATE DATABASE `{restore_database}`")
    print(f"Created database `{restore_database}` for renaming")

rename_command = [
    "mysqldump",
    "-h", host,
    "-P", port,
    "-u", user,
    f"--password={password}",
    database
]
with open(f"/tmp/{database}_to_{restore_database}.sql", "w") as file:
    subprocess.run(rename_command, stdout=file, check=True)

with open(f"/tmp/{database}_to_{restore_database}.sql", "r") as file:
    restore_command = [
        "mysql",
        "-h", host,
        "-P", port,
        "-u", user,
        f"--password={password}",
        restore_database
    ]
    subprocess.run(restore_command, stdin=file, check=True)

print(f"Renamed database `{database}` to `{restore_database}`")

# Step 8: Restore the original `db1_temp` back to `db1`
connection = pymysql.connect(
    host=host,
    port=int(port),
    user=user,
    password=password
)
with connection.cursor() as cursor:
    cursor.execute(f"DROP DATABASE `{database}`")
    print(f"Dropped temporary `{database}`")
    cursor.execute(f"CREATE DATABASE `{database}`")
    print(f"Restored `{database}_temp` to `{database}`")
connection.commit()
connection.close()
