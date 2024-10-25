import os
import shutil
import subprocess
from datetime import datetime

from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from sql.cron import create_backup_cron_job, delete_cron_job, toggle_cron_job
from sql.models import BackupHistory, BackupRoutine, Instance
from sql.utils.resource_group import user_instances

BACKUP_DIR_MANUAL = '/opt/archery/backup/manual'
BACKUP_DIR_MANUAL_MYSQL = '/opt/archery/backup/manual/mysql'
BACKUP_DIR_MANUAL_MONGO = '/opt/archery/backup/manual/mongo'
BACKUP_DIR_AUTO = '/opt/archery/backup/auto'
BACKUP_DIR_AUTO_MYSQL = '/opt/archery/backup/auto/mysql'
BACKUP_DIR_AUTO_MONGO = '/opt/archery/backup/auto/mongo'

# Create the backup directories if they don't exist
os.makedirs(BACKUP_DIR_MANUAL, exist_ok=True)
os.makedirs(BACKUP_DIR_MANUAL_MYSQL, exist_ok=True)
os.makedirs(BACKUP_DIR_MANUAL_MONGO, exist_ok=True)
os.makedirs(BACKUP_DIR_AUTO, exist_ok=True)
os.makedirs(BACKUP_DIR_AUTO_MYSQL, exist_ok=True)
os.makedirs(BACKUP_DIR_AUTO_MONGO, exist_ok=True)

def perform_manual_backup(request):
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

def list_manual_backup_files(request):
    """Handle GET requests and return a list of backup files for MySQL and MongoDB."""
    if request.method == 'GET':
        backup_files = {
            'MySQL': list_backup_files(BACKUP_DIR_MANUAL_MYSQL, is_file=True, file_extension='.sql'),
            'MongoDB': list_backup_files(BACKUP_DIR_MANUAL_MONGO, is_file=False)
        }
        return JsonResponse(backup_files, safe=False)

def list_auto_backup_files(request):
    """Handle GET requests and return a list of backup files for MySQL and MongoDB."""
    if request.method == 'GET':
        backup_files = {
            'MySQL': list_backup_files(BACKUP_DIR_AUTO_MYSQL, is_file=True, file_extension='.sql'),
            'MongoDB': list_backup_files(BACKUP_DIR_AUTO_MONGO, is_file=False)
        }
        return JsonResponse(backup_files, safe=False)

def list_backup_files(backup_dir, is_file=True, file_extension=''):
    """List all backup files or directories, including metadata like size and creation time."""
    backup_list = []
    
    for entry in os.listdir(backup_dir):
        entry_path = os.path.join(backup_dir, entry)
        
        if is_file:
            if os.path.isfile(entry_path) and entry.endswith(file_extension):
                backup_list.append(generate_backup_metadata(entry, entry_path, is_file=True))
        else:
            if os.path.isdir(entry_path):
                backup_list.append(generate_backup_metadata(entry, entry_path, is_file=False))

    return backup_list

def generate_backup_metadata(name, path, is_file):
    """Generate metadata for a backup file or directory."""
    metadata = {
        'name': name,
        'db_name': extract_db_name(name),
        'backup_type': extract_backup_type(name),
        'created_at': datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if is_file:
        metadata['size'] = os.path.getsize(path)
    else:
        metadata['size'] = calculate_directory_size(path)
    
    return metadata

def download_backup(request, file_name, is_auto=False):
    """Download the selected backup file (MySQL .sql or MongoDB folder as .zip)."""
    # Choose the correct directory based on whether the backup is automatic or manual
    if is_auto:
        mysql_backup_dir = BACKUP_DIR_AUTO_MYSQL
        mongo_backup_dir = BACKUP_DIR_AUTO_MONGO
    else:
        mysql_backup_dir = BACKUP_DIR_MANUAL_MYSQL
        mongo_backup_dir = BACKUP_DIR_MANUAL_MONGO
    # Determine if it's MySQL or MongoDB based on the file name
    if file_name.endswith('.sql'):
        # MySQL backup (.sql)
        file_path = os.path.join(mysql_backup_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
        else:
            raise Http404(f"File {file_name} not found")
    
    else:
        # MongoDB backup (directory to be zipped)
        dir_path = os.path.join(mongo_backup_dir, file_name)
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

def perform_backup(instance, backup_type, db_name, table_name=None):
    """Perform a manual backup of the specified database or table."""
    db_type = instance.db_type
    # timestamp example: 2022-10-20_2359
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    # File name format: <dbType>-<backup_type>-<instance_name>-<database_name>-<table_name>-<timestamp>, depending on the backup type, database name and table name can be empty
    
    # backup_file_name = f"{db_type}_{backup_type}_{db_name + '_' if db_name else ''}_{timestamp}"
    backup_file_name = f"{db_type}.{backup_type}.{instance.instance_name}.{db_name + '.' if db_name else ''}{table_name + '.' if table_name else ''}{timestamp}"
    # Ensure the backup directory exists
    os.makedirs(BACKUP_DIR_MANUAL, exist_ok=True)

    try:
        # Backup command for MySQL
        if db_type == 'mysql':
            backup_file_output = os.path.join(BACKUP_DIR_MANUAL_MYSQL, backup_file_name) + '.sql' 
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
            backup_file_output = os.path.join(BACKUP_DIR_MANUAL_MONGO, backup_file_name)
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

def extract_db_name(name):
    """Extract the database name from the file or directory name."""
    parts = name.split('.')
    if len(parts) == 6:
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
    return os.path.join(BACKUP_DIR_MANUAL, file_name)

def create_backup_routine(request):
    """Handles the AJAX request to create a new backup routine."""
    if request.method == "POST":
        # Get data from AJAX POST request
        instance_id = request.POST.get("instance_id")
        backup_type = request.POST.get("backup_type")
        db_name = request.POST.get("db_name", None)
        table_name = request.POST.get("table_name", None)
        interval = request.POST.get("interval")
        time = request.POST.get("time")

        # If time is "", set it to None
        if time == "":
            time = None

        # Fetch the instance
        instance = Instance.objects.get(id=instance_id)
        
        # Create new BackupRoutine
        routine = BackupRoutine.objects.create(
            instance=instance,
            backup_type=backup_type,
            db_name=db_name,
            table_name=table_name,
            interval=interval,
            time=time,
            created_at=datetime.now()
        )
        
        # Try to create a cron job for the backup routine
        # test_create_simple_cron_job()
        create_backup_cron_job(routine)

        # Return the created routine as a JSON response
        return JsonResponse({
            "status": "success",
            "routine": {
                "db_type": instance.db_type,
                "backup_type": routine.backup_type,
                "interval": routine.interval,
                "time": routine.time,
                "status": routine.status
            }
        })

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@require_POST  # Ensures that only POST requests are allowed
def delete_backup_routine(request, id):
    """Deletes the backup routine with the given ID."""
    try:
        # Try to find the backup routine by its ID and delete it
        routine = BackupRoutine.objects.get(id=id)
        routine.delete()

        # Delete the cron job associated with the routine
        delete_cron_job(id)

        return JsonResponse({'status': 'success', 'message': 'Backup routine deleted successfully.'})
    except BackupRoutine.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Backup routine not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST # Ensures that only POST requests are allowed
def toggle_backup_routine(request, id):
    """Toggles the status of the backup routine (active/inactive)."""
    try:
        # Try to find the backup routine by its ID
        routine = BackupRoutine.objects.get(id=id)
        
        # Toggle the status
        if routine.status == 'active':
            routine.status = 'inactive'
        else:
            routine.status = 'active'
        
        routine.save()  # Save the updated status to the database
        # Toggle the cron job status
        toggle_cron_job(routine)

        return JsonResponse({'status': 'success', 'message': f'Backup routine {routine.status} successfully.'})
    
    except BackupRoutine.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Backup routine not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': "from toggle_backup_routine: " + str(e)}, status=500)


def api_backup_routines(request):
    """Fetches the backup routines and returns them as JSON."""
    
    routines = BackupRoutine.objects.all().values(
        'id',            # Unique ID of the routine
        'instance__instance_name',  # Name of the instance
        'db_name',        # Database name (if applicable)
        'table_name',     # Table name (if applicable)
        'backup_type',    # Type of backup (instance, database, table)
        'interval',       # Backup interval (e.g., daily, weekly)
        'time',           # Time when the backup is scheduled
        'status'          # Status of the backup routine (active/inactive)
    )

    # Serializing the QuerySet to a list of dictionaries
    result = {
        "status": "success",
        "data": list(routines)
    }

    return JsonResponse(result)

def api_backup_history(request):
    """Fetches the backup history for the instance."""
    limit = int(request.POST.get("limit", 10))
    offset = int(request.POST.get("offset", 0))
    instance_id = request.POST.get("instance_id")
    search = request.POST.get("search", "")
    
    backups = BackupHistory.objects.filter(instance__id=instance_id)
    
    # If search query exists, filter by database type or other relevant fields
    if search:
        backups = backups.filter(db_type__icontains=search)
    
    backups = backups[offset:offset + limit].values(
        "instance__instance_name", "db_type", "backup_type", "size", "created_at", "status"
    )
    
    # Serialize the data for JSON response
    rows = list(backups)
    result = {
        "status": 0,
        "msg": "Success",
        "data": rows
    }
    
    return JsonResponse(result)

### Unused functions ###
# BACKUP_SETTINGS_FILE = '/opt/archery/backup/backup_settings.json'
# BACKUP_SETTINGS = {
#     # Default backup settings
#     'backup_frequency': 'daily',
#     'backup_time': '00:00',
#     'backup_destination': BACKUP_DIR
# }

# Create a default backup settings file if it doesn't exist
# if not os.path.exists(BACKUP_SETTINGS_FILE):
#     with open(BACKUP_SETTINGS_FILE, 'w') as f:
#         f.write('{"backup_frequency": "daily", "backup_time": "00:00", "backup_destination": "/opt/archery/backup"}')


# def backup_settings(request):
#     """View for saving backup settings."""
#     if request.method == 'POST':
#         frequency = request.POST.get('frequency')
#         time = request.POST.get('time')
#         destination = request.POST.get('destination')

#         # Store the settings (you may want to persist these settings in a file or DB)
#         BACKUP_SETTINGS['frequency'] = frequency
#         BACKUP_SETTINGS['time'] = time
#         BACKUP_SETTINGS['destination'] = destination

#         # Optionally, save the settings to a config file or database
#         save_backup_settings(BACKUP_SETTINGS)

#         return redirect('backup_dashboard')  # Redirect back to the dashboard

#     return render(request, 'backup/backup_settings.html')

# def save_backup_settings(settings):
#     """Save backup settings to a file."""
#     with open(BACKUP_SETTINGS_FILE, 'w') as f:
#         f.write(str(settings))