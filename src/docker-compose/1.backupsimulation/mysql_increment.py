import os
import subprocess
import pymysql
import time
from datetime import datetime

# Load environment variables
mysql_host = os.getenv("MYSQL_HOST")
mysql_user = os.getenv("MYSQL_USER")
mysql_password = os.getenv("MYSQL_PASSWORD")
zip_password = os.getenv("ZIP_PASSWORD")
log_db_host = os.getenv("BACKUP_LOG_DB_HOST")
log_db_user = os.getenv("BACKUP_LOG_DB_USER")
log_db_password = os.getenv("BACKUP_LOG_DB_PASSWORD")
s3_bucket_uri = os.getenv("S3_BUCKET_URI")
s3_access_key = os.getenv("S3_ACCESS_KEY")
s3_secret_key = os.getenv("S3_SECRET_KEY")

# Backup timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_file = f"/backup/mysql_backup_{timestamp}.sql"
zip_file = f"{backup_file}.zip"

# Perform the backup
start_time = time.time()
subprocess.run([
    "mysqldump",
    "-h", mysql_host,
    "-u", mysql_user,
    f"--password={mysql_password}",
    "--all-databases",
    "--single-transaction",
    f"--result-file={backup_file}"
], check=True)

# Zip the backup with a password
subprocess.run(["zip", "-P", zip_password, zip_file, backup_file], check=True)

# Simulate S3 upload
s3_uri = f"{s3_bucket_uri}/{os.path.basename(zip_file)}"
print(f"Fake uploading {zip_file} to {s3_uri}")

# Log backup completion
end_time = time.time()
connection = pymysql.connect(
    host=log_db_host,
    user=log_db_user,
    password=log_db_password,
    database="backup_log_db"  # Use the correct database
)
cursor = connection.cursor()
cursor.execute("""
    INSERT INTO BackupRecord (instance_name, database_type, start_time, end_time, s3_uri)
    VALUES (%s, %s, %s, %s, %s)
""", ("mysql-instance", "MySQL", datetime.fromtimestamp(start_time),
      datetime.fromtimestamp(end_time), s3_uri))
connection.commit()
cursor.close()
connection.close()
