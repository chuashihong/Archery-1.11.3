import subprocess
from .models import RestoreRequest, Instance
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
        unzip_password = request.POST.get('unzip_password')

        # Validate the instance and restore time
        try:
            instance = Instance.objects.get(id=instance_id)
        except Instance.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Instance not found"}, status=404)

        # Create a new restore request
        try:
            restore_request = RestoreRequest.objects.create(
                instance=instance,
                db_name=db_name,
                table_name=table_name,
                restore_time=restore_time,
                unzip_password=unzip_password,
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
        # Fetch all pending restore requests
        pending_requests = RestoreRequest.objects.filter(status="pending").select_related('instance')

        # Prepare the data to be returned as JSON
        data = []
        for request in pending_requests:
            data.append({
                "id": request.id,
                "instance_name": request.instance.instance_name,
                "restore_time": request.restore_time.strftime('%Y-%m-%d %H:%M:%S'),
                "db_name": request.db_name,
                "table_name": request.table_name,
            })

        # Return the JSON response
        return JsonResponse({"status": "success", "requests": data})
    
    # If the request method is not GET, return an error
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
