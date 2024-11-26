import os
import subprocess
from backup_management.interfaces import DatabaseBackupInterface
from sql.models import Instance
class MongoBackup(DatabaseBackupInterface):
    def __init__(self, instance: Instance):
        self.db_host = instance.host
        self.db_port = instance.port
        self.db_user = instance.user
        self.db_password = instance.password
        self.db_name = instance.db_name

    def backup_full(self, backup_path: str) -> None:
        """
        Perform a full backup of the MongoDB instance.
        """
        cmd = [
            "mongodump",
            "--host", self.db_host,
            "--port", str(self.db_port),
            "-u", self.db_user,
            "-p", self.db_password,
            "--authenticationDatabase", "admin",
            "--out", backup_path
        ]
        subprocess.run(cmd)

    def backup_inc(self, backup_path: str, start_time: int, stop_time: int) -> None:
        """
        Perform an incremental backup.
        MongoDB does not have native incremental backup support.
        This function achieves incremental backup by backing up local.oplog.rs within specified timestamps.

        :param backup_path: The path to store the backup files.
        :param start_time: The starting timestamp (UNIX time) for the backup.
        :param stop_time: The ending timestamp (UNIX time) for the backup.
        """
        # Construct the mongodump command
        cmd = [
            "mongodump",
            "--host", self.db_host,
            "--port", str(self.db_port),
            "-u", self.db_user,
            "-p", self.db_password,
            "--authenticationDatabase", "admin",
            "--out", backup_path,
            "-d", "local",  # Target the local database
            "-c", "oplog.rs",  # Target the oplog.rs collection
            "--query", f'{{"ts":{{"$gt":{{"$timestamp":{{"t":{start_time},"i":1}}}},"$lt":{{"$timestamp":{{"t":{stop_time},"i":1}}}}}}}}'
        ]

        # Print the command for debugging purposes
        print("Executing incremental backup with the following command:")
        print(" ".join(cmd))

        # Execute the command
        result = os.system(" ".join(cmd))
        if result != 0:
            raise RuntimeError("Incremental backup failed. Check the logs for details.")
        
    def cleanup_logs(self) -> None:
        pass