# File: archery/backup_utils.py

import os
import subprocess

BACKUP_DIR = '/path/to/backup/dir'

def perform_backup(db_name):
    """Perform the backup of the given database."""
    backup_file = f"{BACKUP_DIR}/{db_name}_backup_$(date +%F_%T).dump"
    try:
        if db_name == 'mysql':
            # Use mysqldump to perform backup
            command = f"mysqldump -u root -p'yourpassword' --all-databases > {backup_file}"
        elif db_name == 'mongodb':
            # Use mongodump to perform backup
            command = f"mongodump --out {backup_file}"

        subprocess.run(command, shell=True, check=True)
        return True, f"Backup successful. File: {backup_file}"
    except subprocess.CalledProcessError as e:
        return False, str(e)

def list_backup_files():
    """List all backup files in the backup directory."""
    return os.listdir(BACKUP_DIR)

def download_backup_file(file_name):
    """Return the full path to the backup file for download."""
    return os.path.join(BACKUP_DIR, file_name)
