# backup_management/implementations/mysql_backup.py
import os
import subprocess
from backup_management.interfaces import DatabaseBackupInterface
from sql.models import Instance
class MySQLBackup(DatabaseBackupInterface):
    def __init__(self, instance: Instance):
        self.host = instance.host
        self.port = instance.port
        self.user = instance.user
        self.password = instance.password
        self.database = instance.db_name
        
    def backup_full(self, backup_path: str) -> None:
        """
        Performs a full dump (all databases) and writes the output to a destination.
        """
        cmd = f"mysqldump -h {self.host} -P {self.port} -u {self.user} -p{self.password} --all-databases > {backup_path}"
        subprocess.run(cmd, shell=True)

    def backup_inc(self, backup_path: str) -> None:
        """
        Act as a slave and pull binlog from database, use binlog2sql to convert binlog to sql, and write the output to a destination.
        """
        cmd = f"mysqlbinlog --read-from-remote-server --host={self.host} --user={self.user} --password={self.password} --result-file={backup_path}"
        subprocess.run(cmd, shell=True)

    def cleanup_logs(self) -> None:
        pass