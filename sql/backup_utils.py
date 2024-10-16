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

def perform_backup(db_name):
    """Perform a manual backup."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file = f"{BACKUP_DIR}/{db_name}_backup_{timestamp}.dump"
    
    try:
        if db_name == 'mysql':
            command = f"mysqldump -u root -p'yourpassword' --all-databases > {backup_file}"
        elif db_name == 'mongodb':
            command = f"mongodump --out {backup_file}"

        subprocess.run(command, shell=True, check=True)
        return True, f"Backup successful: {backup_file}"
    except subprocess.CalledProcessError as e:
        return False, str(e)

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
