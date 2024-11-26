# backup_management/backup_manager.py
from backup_management.implementations.mysql_backup import MySQLBackup
from backup_management.implementations.mongo_backup import MongoBackup
from sql.models import Instance

class BackupManager:
    def __init__(self, instace: Instance):
        self.instace = instace
        self.db_backup = self._get_backup_implementation()

    def _get_backup_implementation(self):
        if self.instance.db_type == "mysql":
            return MySQLBackup(self.instance)
        elif self.instance.db_type == "mongo":
            return MongoBackup(self.instance)
        ### Add more in future
        # elif self.instance.db_type == "redis":
        #     return RedisBackup(self.instance)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def perform_backup(self, backup_type: str, target_path: str) -> None:
        self.db_backup.backup(backup_type, target_path)

    def perform_restore(self, backup_file: str) -> None:
        self.db_backup.restore(backup_file)