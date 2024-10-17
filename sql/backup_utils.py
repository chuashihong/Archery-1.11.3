import os
import subprocess
from datetime import datetime

BACKUP_DIR = '/opt/archery/backup'

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

BACKUP_SETTINGS_FILE = '/opt/archery/backup/backup_settings.json'

if not os.path.exists(BACKUP_SETTINGS_FILE):
    with open(BACKUP_SETTINGS_FILE, 'w') as f:
        f.write('{"backup_frequency": "daily", "backup_time": "00:00", "backup_destination": "/opt/archery/backup"}')

def save_backup_settings(settings):
    """Save backup settings to a file."""
    with open(BACKUP_SETTINGS_FILE, 'w') as f:
        f.write(str(settings))

def perform_backup(backup_type, db_type, db_name, table_name=None):
    """Perform a manual backup of the specified database or table."""
    timestamp = datetime.now().strftime("%Y-%b-%d-%H:%M:%S")
    backup_file = os.path.join(BACKUP_DIR, f"{db_type}-{db_name + '-' if db_name else ''}backup-{timestamp}")
    
    # Ensure the backup directory exists
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    try:
        # Backup command for MySQL
        if db_type == 'mysql':
            backup_file += ".sql"  # Ensuring correct file extension
            if backup_type == "instance":
                # Backup the entire MySQL instance
                command = ["mysqldump", "-h", "host.docker.internal", "-P", "3307", "-u", "root", "-ppassword123", "--all-databases"]
            elif backup_type == "database":
                # Backup a specific MySQL database
                command = ["mysqldump", "-h", "host.docker.internal", "-P", "3307", "-u", "root", "-ppassword123", db_name]
            elif backup_type == "table":
                # Backup a specific table from a database
                command = ["mysqldump", "-h", "host.docker.internal", "-P", "3307", "-u", "root", "-ppassword123", db_name, table_name]
            else:
                return False, "Invalid backup type specified for MySQL."

            # Direct the output to the backup file for MySQL
            with open(backup_file, 'w') as f:
                subprocess.run(command, stdout=f, check=True)
            
        # Backup command for MongoDB
        elif db_type == 'mongo':
            # Common parameters for all MongoDB backups (host, port, user, password)
            common_mongo_args = [
                "mongodump", 
                "--host", "host.docker.internal", 
                "--port", "27018", 
                "-u", "admin", 
                "-p", "password123", 
                "--authenticationDatabase", "admin"
            ]
            
            if backup_type == "instance":
                # Backup the entire MongoDB instance
                command = common_mongo_args + ["--out", backup_file]
            
            elif backup_type == "database":
                # Backup a specific MongoDB database
                command = common_mongo_args + ["--db", db_name, "--out", backup_file]
            
            elif backup_type == "table":
                # Backup a specific collection from a MongoDB database
                command = common_mongo_args + ["--db", db_name, "--collection", table_name, "--out", backup_file]
            
            else:
                return False, "Invalid backup type specified for MongoDB."

            # Run the MongoDB backup command
            subprocess.run(command, check=True)
        else:
            return False, "Unsupported database type."

        return True, f"Backup successful: {backup_file}"

    except subprocess.CalledProcessError as e:
        return False, f"Backup failed: {str(e)}"

    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"
def list_backup_files():
    """List all backup files."""
    backup_files = []
    for filename in os.listdir(BACKUP_DIR):
        filepath = os.path.join(BACKUP_DIR, filename)
        if os.path.isfile(filepath):
            backup_files.append({
                'name': filename,
                'db_name': 'MySQL' if 'mysql' in filename else 'MongoDB',
                'created_at': datetime.fromtimestamp(os.path.getctime(filepath))
            })
    return backup_files

def download_backup_file(file_name):
    """Return the full path to the backup file."""
    return os.path.join(BACKUP_DIR, file_name)
