# backup_management/interfaces.py
from abc import ABC, abstractmethod

class DatabaseBackupInterface(ABC):
    @abstractmethod
    def backup_full(self, backup_path: str) -> None:
        """Perform a full backup"""
        pass

    @abstractmethod
    def backup_inc(self, backup_path:str, *args, **kwargs) -> None:
        """Perform an incremental backup."""
        pass      

    @abstractmethod
    def cleanup_logs(self) -> None:
        """
        Clean up binlogs and other logs.
        """
        pass

class DatabaseRestoreInterface(ABC):
    @abstractmethod
    def restore(self, backup_path: str) -> None:
        pass

class BackupHandlerInterface(ABC):
    @abstractmethod
    def compress_and_encrypt(self, input_file: str, output_file: str, password: str) -> None:
        """
        Compress and encrypt a file.

        :param input_file: The file to compress and encrypt.
        :param output_file: The output file.
        :param password: The password to use for encryption.
        """
        pass
    
    @abstractmethod
    def upload_to_s3(self, file_path: str, bucket_name: str) -> None:
        """
        Upload a file to an S3 bucket.

        :param file_path: The file to upload.
        :param bucket_name: The name of the S3 bucket.
        """
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file.

        :param file_path: The file to delete.
        """
        pass

class RestoreHandlerInterface(ABC):
    @abstractmethod
    def retrieve_from_s3(self, bucket_name: str, key: str, output_path: str) -> None:
        """
        Retrieve a file from an S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        :param key: The key of the file in the bucket.
        :param output_path: The path to save the file to.
        """
        pass

    @abstractmethod
    def decrypt_and_decompress(self, input_file: str, output_file: str, password: str) -> None:
        """
        Decrypt and decompress a file.

        :param input_file: The file to decrypt and decompress.
        :param output_file: The output file.
        :param password: The password to use for decryption.
        """
        pass
    
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file.

        :param file_path: The file to delete.
        """
        pass