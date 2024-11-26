# backup_management/scheduler.py
from django_q.tasks import schedule
from datetime import timedelta

def schedule_backup(manager: "BackupManager", backup_type: str, target_path: str, interval_hours: int):
    schedule(
        func=manager.perform_backup,
        args=[backup_type, target_path],
        schedule_type="H",
        minutes=interval_hours * 60,
    )