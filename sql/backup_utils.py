import os
import shutil
import subprocess
from datetime import datetime

from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from sql.models import Instance
from sql.utils.resource_group import user_instances

BACKUP_DIR = '/opt/archery/backup'
BACKUP_DIR_MYSQL = '/opt/archery/backup/mysql'
BACKUP_DIR_MONGO = '/opt/archery/backup/mongo'

# Create the backup directories if they don't exist
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR_MYSQL, exist_ok=True)
os.makedirs(BACKUP_DIR_MONGO, exist_ok=True)

BACKUP_SETTINGS_FILE = '/opt/archery/backup/backup_settings.json'
BACKUP_SETTINGS = {
    # Default backup settings
    'backup_frequency': 'daily',
    'backup_time': '00:00',
    'backup_destination': BACKUP_DIR
}

# Create a default backup settings file if it doesn't exist
if not os.path.exists(BACKUP_SETTINGS_FILE):
    with open(BACKUP_SETTINGS_FILE, 'w') as f:
        f.write('{"backup_frequency": "daily", "backup_time": "00:00", "backup_destination": "/opt/archery/backup"}')


def backup_settings(request):
    """View for saving backup settings."""
    if request.method == 'POST':
        frequency = request.POST.get('frequency')
        time = request.POST.get('time')
        destination = request.POST.get('destination')

        # Store the settings (you may want to persist these settings in a file or DB)
        BACKUP_SETTINGS['frequency'] = frequency
        BACKUP_SETTINGS['time'] = time
        BACKUP_SETTINGS['destination'] = destination

        # Optionally, save the settings to a config file or database
        save_backup_settings(BACKUP_SETTINGS)

        return redirect('backup_dashboard')  # Redirect back to the dashboard

    return render(request, 'backup/backup_settings.html')

def manual_backup(request):
    """Trigger a manual backup of the selected database or table."""
    if request.method == 'POST':
        backup_type = request.POST.get("backup_type")
        instance_id = request.POST.get("instance_id", 0)
        db_name = request.POST.get("db_name")
        table_name = request.POST.get("table_name")
        try:
            instance = user_instances(request.user, db_type=["mysql", "mongo"]).get(id=instance_id)
        except Instance.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Instance not found.'}, status=404)
        
        # Perform the backup, optionally including the table name
        success, message = perform_backup(instance, backup_type, db_name, table_name)
        return JsonResponse({'success': success, 'message': message})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

def backup_files(request):
    if request.method == 'GET':
        backup_files = list_backup_files()
        return JsonResponse(backup_files, safe=False)

def download_backup(request, file_name):
    """Download the selected backup file (MySQL .sql or MongoDB folder as .zip)."""
    
    # Determine if it's MySQL or MongoDB based on the file name
    if file_name.endswith('.sql'):
        # MySQL backup (.sql)
        file_path = os.path.join(BACKUP_DIR_MYSQL, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
        else:
            raise Http404(f"File {file_name} not found")
    
    else:
        # MongoDB backup (directory to be zipped)
        dir_path = os.path.join(BACKUP_DIR_MONGO, file_name)
        if os.path.exists(dir_path):
            # Compress the directory into a .zip file
            zip_path = f"{dir_path}.zip"
            shutil.make_archive(dir_path, 'zip', dir_path)
            
            with open(zip_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{file_name}.zip"'
                return response
        else:
            raise Http404(f"Directory {file_name} not found")


def save_backup_settings(settings):
    """Save backup settings to a file."""
    with open(BACKUP_SETTINGS_FILE, 'w') as f:
        f.write(str(settings))

def perform_backup(instance, backup_type, db_name, table_name=None):
    """Perform a manual backup of the specified database or table."""
    db_type = instance.db_type
    # timestamp example: 2022-10-20_2359
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    # File name format: <dbType>-<backup_type>-<instance_name>-<database_name>-<table_name>-<timestamp>, depending on the backup type, database name and table name can be empty
    
    # backup_file_name = f"{db_type}_{backup_type}_{db_name + '_' if db_name else ''}_{timestamp}"
    backup_file_name = f"{db_type}.{backup_type}.{instance.instance_name}.{db_name + '.' if db_name else ''}{table_name + '.' if table_name else ''}{timestamp}"
    # Ensure the backup directory exists
    os.makedirs(BACKUP_DIR, exist_ok=True)

    try:
        # Backup command for MySQL
        if db_type == 'mysql':
            backup_file_output = os.path.join(BACKUP_DIR_MYSQL, backup_file_name) + '.sql' 
            command = ["mysqldump",  
                       "-h", instance.host,
                       "-P", str(instance.port),
                       "-u", instance.user, 
                       "-p" + instance.password]
            if backup_type == "instance":
                # Backup the entire MySQL instance
                command += ["--all-databases"]
            elif backup_type == "database":
                # Backup a specific MySQL database
                command += [db_name]
            elif backup_type == "table":
                # Backup a specific table from a database
                command += [db_name, table_name]
            else:
                return False, "Invalid backup type specified for MySQL."

            # Direct the output to the backup file for MySQL
            with open(backup_file_output, 'w') as f:
                subprocess.run(command, stdout=f, check=True)
            
        # Backup command for MongoDB
        elif db_type == 'mongo':
            backup_file_output = os.path.join(BACKUP_DIR_MONGO, backup_file_name)
            command = [
                "mongodump", 
                "--host", instance.host,
                "--port", str(instance.port),
                "-u", instance.user,
                "-p", instance.password, 
                #TODO: need to clarify the authentication database 
                "--authenticationDatabase", "admin"
            ]
            
            if backup_type == "instance":
                # Backup the entire MongoDB instance
                command += ["--out", backup_file_output]
            
            elif backup_type == "database":
                # Backup a specific MongoDB database
                command += ["--db", db_name, "--out", backup_file_output]
            
            elif backup_type == "table":
                # Backup a specific collection from a MongoDB database
                command += ["--db", db_name, "--collection", table_name, "--out", backup_file_output]
            
            else:
                return False, "Invalid backup type specified for MongoDB."

            # Run the MongoDB backup command
            subprocess.run(command, check=True)
        else:
            # If the database type is not supported
            return False, "Unsupported database type."

        return True, f"Backup successful: {backup_file_output}"

    except subprocess.CalledProcessError as e:
        return False, f"Backup failed: {str(e)}"

    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"

def list_backup_files():
    """List all backup files for MySQL and MongoDB, including metadata like size and creation time."""
    backup_files = {
        'MySQL': [],
        'MongoDB': []
    }

    # List MySQL backup files (.sql files)
    for filename in os.listdir(BACKUP_DIR_MYSQL):
        filepath = os.path.join(BACKUP_DIR_MYSQL, filename)
        if os.path.isfile(filepath) and filename.endswith('.sql'):
            backup_files['MySQL'].append({
                'name': filename,
                'db_name': extract_db_name(filename),
                'backup_type': extract_backup_type(filename),  # Extract backup type (instance, db, or table)
                'size': os.path.getsize(filepath),  # File size in bytes
                'created_at': datetime.fromtimestamp(os.path.getctime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
            })

    # List MongoDB backup directories (folders)
    for dirname in os.listdir(BACKUP_DIR_MONGO):
        dirpath = os.path.join(BACKUP_DIR_MONGO, dirname)
        if os.path.isdir(dirpath):
            backup_files['MongoDB'].append({
                'name': dirname,
                'db_name': extract_db_name(dirname),  # Extract db name
                'backup_type': extract_backup_type(dirname),  # Extract backup type (instance, db, or collection)
                'size': calculate_directory_size(dirpath),  # Calculate folder size
                'created_at': datetime.fromtimestamp(os.path.getctime(dirpath)).strftime("%Y-%m-%d %H:%M:%S")
            })

    return backup_files

def extract_db_name(name):
    """Extract the database name from the file or directory name."""
    parts = name.split('.')
    if len(parts) > 3:
        return parts[3]  # The db_name should be the 4th part (0-indexed)
    return "Unknown"

def extract_backup_type(name):
    """Extract the type of backup from the file or directory name."""
    parts = name.split('.')
    if len(parts) > 1:
        return parts[1]  # The backup type is the 2nd part (0-indexed)
    return "Unknown"

def calculate_directory_size(directory):
    """Calculate the total size of a directory in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def download_backup_file(file_name):
    """Return the full path to the backup file."""
    return os.path.join(BACKUP_DIR, file_name)
