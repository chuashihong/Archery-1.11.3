import os
import subprocess
import time
from datetime import datetime

# MySQL backup configuration
mysql_host = "localhost"
mysql_port = "3309"
mysql_user = "root"
mysql_password = "chuashihong"
backup_dir = "./backup"

# Generate backup file name
now = datetime.now()
timestamp = now.strftime("%Y-%m-%d_%H-%M")
backup_file = os.path.join(backup_dir, f"mysql_backup_{timestamp}.sql")

try:
    # Ensure the backup directory exists
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"Created directory: {backup_dir}")

    # Perform the MySQL dump
    subprocess.run([
        "mysqldump",
        "-h", mysql_host,
        "-P", mysql_port,
        "-u", mysql_user,
        f"--password={mysql_password}",
        "--all-databases",
        "--single-transaction",
        f"--result-file={backup_file}"
    ], check=True)
    print(f"Backup file created: {backup_file}")

except subprocess.CalledProcessError as e:
    print(f"Error during backup process: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
