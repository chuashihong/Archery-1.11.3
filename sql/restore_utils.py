import subprocess
import boto3
import os
from datetime import datetime

import pymysql
from .models import IncBackupRecord, RestoreRequest, Instance
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def generate_restore_command(restore_request):
    """
    Generates the restore command to be executed based on the restore request.
    """
    instance = restore_request.instance
    restore_time = restore_request.restore_time.strftime('%Y-%m-%d-%H:%M:%S')
    command = (
        f"python restore.py "
        f"--restore_time \"{restore_time}\" "
        f"--region \"your-region\" "
        f"--key \"your-aws-key\" "
        f"--secret \"your-aws-secret\" "
        f"--unzip \"{restore_request.unzip_password}\" "
        f"--host1 \"{instance.host}\" "
        f"--user \"{instance.user}\" "
        f"--password \"{instance.password}\" "
        f"--bucket \"{restore_request.s3_bucket_file_path.split('/')[0]}\" "
        f"--all_folder \"{restore_request.s3_bucket_file_path}\""
    )
    return command


def execute_restore_plan(restore_request):
    """
    Executes the restore command generated from the restore request.
    Updates the request status and outcome based on the execution result.
    """
    if restore_request.status != 'approved':
        return "Restore request is not approved."

    command = generate_restore_command(restore_request)
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        restore_request.status = 'completed'
        restore_request.outcome = result.stdout
    except subprocess.CalledProcessError as e:
        restore_request.status = 'failed'
        restore_request.outcome = e.stderr
    finally:
        restore_request.save()
    return restore_request.outcome


def find_backup(instance_name, restore_time):
    """
    Finds a backup record matching the given instance name and restore time.
    Returns the backup record or None if no match is found.
    """
    from .models import IncBackupRecord  # Import here to avoid circular dependency
    return IncBackupRecord.objects.filter(
        instance_name=instance_name,
        backup_start_time__lte=restore_time,
        backup_end_time__gte=restore_time,
    ).first()


def approve_restore_request(request_id):
    """
    Approves the restore request and prepares for execution.
    """
    restore_request = RestoreRequest.objects.get(id=request_id)
    restore_request.status = 'approved'
    restore_request.save()
    return restore_request


def reject_restore_request(request_id):
    """
    Rejects the restore request.
    """
    restore_request = RestoreRequest.objects.get(id=request_id)
    restore_request.status = 'rejected'
    restore_request.save()
    return restore_request


def notify_user(restore_request, notification_function):
    """
    Sends a notification to the user about the restore request status and outcome.
    """
    subject = f"Restore Request #{restore_request.id} - {restore_request.status.capitalize()}"
    message = (
        f"Restore request for instance {restore_request.instance.instance_name} has been processed.\n\n"
        f"Status: {restore_request.status}\n\nOutcome:\n{restore_request.outcome}"
    )
    recipient = "user@example.com"  # Replace with actual user email
    notification_function(subject, message, recipient)


@csrf_exempt
def restore_request_create(request):
    if request.method == 'POST':
        instance_id = request.POST.get('instance_id')
        db_name = request.POST.get('db_name')
        table_name = request.POST.get('table_name')
        restore_time = request.POST.get('restore_time')

        # Validate the instance and restore time
        try:
            instance = Instance.objects.get(id=instance_id)
        except Instance.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Instance not found"}, status=404)

        # Create a new restore request
        try:
            RestoreRequest.objects.create(
                instance=instance,
                db_name=db_name,
                table_name=table_name,
                restore_time=restore_time,
                status="pending"
            )
            return JsonResponse({"status": "success", "message": "Restore request created successfully"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

def get_pending_restore_requests(request):
    """
    Returns a list of pending restore requests in JSON format.
    """
    if request.method == 'GET':
        pending_requests = RestoreRequest.objects.filter(status="pending").select_related('instance')

        data = []
        for req in pending_requests:
            data.append({
                "id": req.id,
                "instance_name": req.instance.instance_name,
                "db_name": req.db_name,
                "table_name": req.table_name or "All Tables",
                "restore_time": req.restore_time.strftime('%Y-%m-%d %H:%M:%S') if req.restore_time else None,
                "status": req.status,
                "created_at": req.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "updated_at": req.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return JsonResponse({"status": "success", "requests": data})

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

from django.http import JsonResponse
from .models import RestoreRequest, IncBackupRecord, Instance

def get_restore_execution_details(request, request_id):
    """
    Fetch details for executing a restore request and generate the Python command preview.
    """
    try:
        # Get the restore request 
        restore_request = RestoreRequest.objects.get(id=request_id)
        
        # Get the Instance for this restore
        instance = Instance.objects.get(id=restore_request.instance_id)

        # Fetch restore time from the request
        restore_time = restore_request.restore_time
        if not restore_time:
            return JsonResponse({"status": "error", "message": "Restore time not specified"}, status=400)

        # Fetch the corresponding backup record (To get the S3 details)
        backup_record = IncBackupRecord.objects.filter(
            instance_name=instance.instance_name,
            database_type=instance.db_type,
            start_time__lte=restore_time,
            end_time__gte=restore_time
        ).first()

        if not backup_record:
            return JsonResponse({"status": "error", "message": "No matching backup record found"})

        # Construct the Python command
        # LOGDB_PASSWORD=chuashihong
        # S3_ACCESS_KEY=chuashihong
        # S3_SECRET_KEY=chuashihong
        # ZIP_PASSWORD=chuashihong
        s3_access_key = os.getenv("S3_ACCESS_KEY")
        s3_secret_key = os.getenv("S3_SECRET_KEY")
        zip_password = os.getenv("ZIP_PASSWORD")
        command = (
            f"python mysql_restore.py -r "
            f"--datasource='{backup_record.s3_uri}' "
            f"--region 'your-region' "
            f"--key {s3_access_key} "
            f"--secret {s3_secret_key} "
            f"--host '{instance.host}' "
            f"--port '{instance.port}' "
            f"--user '{instance.user}' "
            f"--zip_password '{zip_password}'"
            f"--password '{instance.password}' "
            f"--db_name '{restore_request.db_name}' "
            f"--table '{restore_request.table_name or ''}'"
        )

        # Return the response with the generated command and details
        return JsonResponse({
            "status": "success",
            "command": command,
            "instance_name": instance.instance_name,
            "db_name": restore_request.db_name,
            "table_name": restore_request.table_name,
            "s3_uri":backup_record.s3_uri,
            "region": "your-region",
            "key": s3_access_key,
            "secret": s3_secret_key,
            "host": instance.host,
            "port": instance.port,
            "user": instance.user,
            "password": instance.password,

        })

    except RestoreRequest.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Restore request not found"}, status=404)


def restore_backup(request):
    if request.method == "POST":
        # Retrieve data from AJAX request
        instance = request.POST.get("instance")
        database = request.POST.get("database")
        table = request.POST.get("table")
        s3_uri = request.POST.get("s3Uri")
        region = request.POST.get("region")
        key = request.POST.get("key")
        secret = request.POST.get("secret")
        host = request.POST.get("host")
        port = request.POST.get("port")
        user = request.POST.get("user")
        password = request.POST.get("password")
        zip_password = os.getenv("ZIP_PASSWORD")
        
        # Generate a timestamped database name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        restore_database = f"{database}_{timestamp}"
        
        try:
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

            # Modify SQL dump file to use `db1_{timestamp}`
            local_sql_path = f"{object_key.split('/')[-1]}".replace(".zip", ".sql")
            backup_file = os.path.join(extraction_dir, f"mysql_backup_{local_sql_path}")
            modified_file = os.path.join(extraction_dir, f"{restore_database}.sql")

            with open(backup_file, "r") as infile, open(modified_file, "w") as outfile:
                for line in infile:
                    # Replace "USE db1" with "USE db1_{timestamp}"
                    if line.strip().startswith("USE "):
                        line = line.replace(f"USE `{database}`", f"USE `{restore_database}`")
                    outfile.write(line)
            print(f"Modified SQL file saved to `{modified_file}`")

            # Create the new database `db1_{timestamp}`
            connection = pymysql.connect(
                host=host,
                port=int(port),
                user=user,
                password=password
            )
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE `{restore_database}`")
                print(f"Created new database `{restore_database}`")
            connection.commit()
            connection.close()

            # Restore the backup to the new database
            restore_command = [
                "mysql",
                "-h", host,
                "-P", port,
                "-u", user,
                f"--password={password}",
                restore_database
            ]
            with open(modified_file, "r") as sql_file:
                subprocess.run(restore_command, stdin=sql_file, check=True)
            print(f"Restored backup to `{restore_database}`")

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


            return JsonResponse({"status": "success", "message": f"Restored to {restore_database}.{restored_table_name}"})
        
        except Exception as e:
            print(f"Error during restore: {e}")
            return JsonResponse({"status": "error", "message": str(e)})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method."})