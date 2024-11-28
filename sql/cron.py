import os
import json

from crontab import CronTab
from datetime import datetime

AUTOMATED_BACKUP_DIR = '/opt/archery/backup/auto'
AUTOMATED_BACKUP_DIR_MYSQL = '/opt/archery/backup/auto/mysql'
AUTOMATED_BACKUP_DIR_MONGO = '/opt/archery/backup/auto/mongo'
CRONJOBS_FILE = os.path.join(AUTOMATED_BACKUP_DIR, 'cronjobs.json')
TIMESTAMP_FORMAT = "$(date +%Y-%m-%d_%H%M)"

# Ensure backup directory exists
os.makedirs(AUTOMATED_BACKUP_DIR, exist_ok=True)
os.makedirs(AUTOMATED_BACKUP_DIR_MYSQL, exist_ok=True)
os.makedirs(AUTOMATED_BACKUP_DIR_MONGO, exist_ok=True)

def create_cron_job(command, schedule_time, comment):
    """
    Create a new cron job with the specified command, schedule time, and a unique comment.
    """
    cron = CronTab(user=True)

    # Escape the % symbols for cron
    # escaped_command = command.replace('%', '\%')
    job = cron.new(command=command, comment=comment)
    job.setall(schedule_time)
    cron.write()

def delete_cron_job(id):
    """
    Deletes the cron job associated with the given backup routine.
    """
    cron = CronTab(user=True)
    # Assuming the cron command is identifiable by routine ID in some way (included in the command)
    for job in cron:
        if int(job.comment) == id:
            cron.remove(job)
            cron.write()
            return True
    return False

def toggle_cron_job(routine):
    """
    Toggles the cron job status (comment/uncomment) based on the backup routine status.
    """
    cron = CronTab(user=True)
    job_found = False

    # Find the cron job associated with the routine by using its ID in the comment
    for job in cron:
        if str(routine.id) in job.comment:
            job_found = True
            if routine.status == 'inactive':
                job.enable(False)  # Comment the job (disable it)
            else:
                job.enable(True)  # Uncomment the job (reactivate it)
            cron.write()
            break

    if not job_found and routine.status == 'active':
        # If no job found and the routine is active, recreate the cron job
        create_backup_cron_job(routine)

def create_backup_cron_job(routine):
    """
    Creates a cron job for the backup routine and stores it with a unique name.
    """
    instance = routine.instance
    db_type = instance.db_type
    backup_type = routine.backup_type
    db_name = routine.db_name
    table_name = routine.table_name
    interval = routine.interval
    time = routine.time
    
    # Generate a unique backup file name
    backup_file_name = generate_unique_backup_name(instance, db_type, backup_type, db_name, table_name)
    
    # Generate backup command
    if db_type == 'mysql':
        command = generate_mysql_backup_command(instance, backup_type, db_name, table_name, backup_file_name)
    elif db_type == 'mongo':
        command = generate_mongo_backup_command(instance, backup_type, db_name, table_name, backup_file_name)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
    
    # Convert interval and time to cron format
    schedule_time = generate_cron_schedule(interval, time)
    
    # Create the cron job
    create_cron_job(command, schedule_time, comment=str(routine.id))
    
    # Store cron job information
    # store_cron_job_info(routine, command, schedule_time)
    
def generate_unique_backup_name(instance, db_type, backup_type, db_name=None, table_name=None):
    """
    Generates a unique backup file/folder name using routine details and a timestamp.
    """
    file_name = f"{db_type}.{backup_type}.{instance.instance_name}"
    
    if db_name:
        file_name += f".{db_name}"
    if table_name:
        file_name += f".{table_name}"
    
    # Add timestamp to ensure unique filenames when multiple backups are scheduled
    file_name += f".{TIMESTAMP_FORMAT}"

    if db_type == 'mysql':
        return os.path.join(AUTOMATED_BACKUP_DIR_MYSQL, file_name)
    elif db_type == 'mongo':
        return os.path.join(AUTOMATED_BACKUP_DIR_MONGO, file_name)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def store_cron_job_info(routine, command, schedule_time):
    """
    Stores cron job information in a JSON file for tracking.
    """
    cronjob_data = {
        "routine_id": routine.id,
        "instance": routine.instance.instance_name,
        "db_type": routine.instance.db_type,
        "backup_type": routine.backup_type,
        "db_name": routine.db_name,
        "table_name": routine.table_name,
        "command": command,
        "schedule_time": schedule_time,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Load existing cron jobs from file
    if os.path.exists(CRONJOBS_FILE):
        with open(CRONJOBS_FILE, 'r') as f:
            cronjobs = json.load(f)
    else:
        cronjobs = []
    
    # Append new cron job info
    cronjobs.append(cronjob_data)
    
    # Write back to the file
    with open(CRONJOBS_FILE, 'w') as f:
        json.dump(cronjobs, f, indent=4)

def generate_mysql_backup_command(instance, backup_type, db_name, table_name, backup_file_name):
    """
    Generates the mysqldump command based on the backup type, outputting to the unique backup file.
    """
    command = f"mysqldump -h {instance.host} -P {instance.port} -u {instance.user} -p{instance.password}"
        
    if backup_type == 'instance':
        command += f" --all-databases > {backup_file_name}.sql"
    elif backup_type == 'database' and db_name:
        command += f" {db_name} > {backup_file_name}.sql"
    elif backup_type == 'table' and db_name and table_name:
        command += f" {db_name} {table_name} > {backup_file_name}.sql"
    return command

def generate_mongo_backup_command(instance, backup_type, db_name, table_name, backup_file_name):
    """
    Generates the mongodump command based on the backup type, outputting to the unique backup folder.
    """
    command = f"mongodump --host {instance.host} --port {instance.port} -u {instance.user} -p {instance.password} --authenticationDatabase admin"
    
    if backup_type == 'instance':
        command += f" --out {backup_file_name}"
    elif backup_type == 'database' and db_name:
        command += f" --db {db_name} --out {backup_file_name}"
    elif backup_type == 'table' and db_name and table_name:
        command += f" --db {db_name} --collection {table_name} --out {backup_file_name}"

    return command
def generate_cron_schedule(interval, time):
    """
    Converts the interval and time into a cron expression.
    """
    # Default time if not specified
    if not time:
        time = datetime.now().strftime('%H:%M')

    hour, minute = map(int, time.split(':'))

    # Map the interval to a cron schedule
    if interval == 'minutely':
        return f"* * * * *"
    elif interval == 'hourly':
        return f"{minute} * * * *"
    elif interval == 'daily':
        return f"{minute} {hour} * * *"
    elif interval == 'weekly':
        return f"{minute} {hour} * * 0"  # 0 represents Sunday
    elif interval == 'monthly':
        return f"{minute} {hour} 1 * *"  # First day of every month
    else:
        raise ValueError(f"Unsupported interval: {interval}")
