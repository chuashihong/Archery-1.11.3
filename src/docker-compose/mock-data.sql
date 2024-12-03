-- Drop database if it exists
DROP DATABASE IF EXISTS `mockdata`;

-- Create the database schema and users
CREATE DATABASE `mockdata`;
USE `mockdata`;
DROP TABLE IF EXISTS IncBackupRecord;

CREATE TABLE IncBackupRecord (
    id INT AUTO_INCREMENT PRIMARY KEY,
    db_type VARCHAR(50) NOT NULL,
    instance_name VARCHAR(100) NOT NULL,
    backup_start_time DATETIME NOT NULL,
    backup_end_time DATETIME NOT NULL,
    s3_bucket_file_path VARCHAR(255) NOT NULL,
    s3_uri VARCHAR(255) NOT NULL
);

-- Insert mock data into the table
INSERT INTO IncBackupRecord (db_type, instance_name, backup_start_time, backup_end_time, s3_bucket_file_path, s3_uri)
VALUES
    ('mysql', 'prd-mysql-tapo-aps-1', '2024-11-28 01:00:00', '2024-11-28 02:00:00', 'backups/mysql/prd-mysql-tapo-aps-1/2024-11-28_01-02.zip', 's3://my-backup-bucket/backups/mysql/prd-mysql-tapo-aps-1/2024-11-28_01-02.zip'),
    ('mysql', 'prd-mysql-tapo-aps-2', '2024-11-28 02:00:00', '2024-11-28 03:00:00', 'backups/mysql/prd-mysql-tapo-aps-2/2024-11-28_02-03.zip', 's3://my-backup-bucket/backups/mysql/prd-mysql-tapo-aps-2/2024-11-28_02-03.zip'),
    ('mysql', 'prd-mysql-tapo-aps-3', '2024-11-28 03:00:00', '2024-11-28 04:00:00', 'backups/mysql/prd-mysql-tapo-aps-3/2024-11-28_03-04.zip', 's3://my-backup-bucket/backups/mysql/prd-mysql-tapo-aps-3/2024-11-28_03-04.zip'),
    ('mysql', 'prd-mysql-tapo-aps-4', '2024-11-28 04:00:00', '2024-11-28 05:00:00', 'backups/mysql/prd-mysql-tapo-aps-4/2024-11-28_04-05.zip', 's3://my-backup-bucket/backups/mysql/prd-mysql-tapo-aps-4/2024-11-28_04-05.zip'),
    ('mysql', 'prd-mysql-tapo-aps-5', '2024-11-28 05:00:00', '2024-11-28 06:00:00', 'backups/mysql/prd-mysql-tapo-aps-5/2024-11-28_05-06.zip', 's3://my-backup-bucket/backups/mysql/prd-mysql-tapo-aps-5/2024-11-28_05-06.zip'),
    ('mongo', 'prd-mongo-tapo-aps-1', '2024-11-28 01:00:00', '2024-11-28 02:00:00', 'backups/mongo/prd-mongo-tapo-aps-1/2024-11-28_01-02.zip', 's3://my-backup-bucket/backups/mongo/prd-mongo-tapo-aps-1/2024-11-28_01-02.zip'),
    ('mongo', 'prd-mongo-tapo-aps-2', '2024-11-28 02:00:00', '2024-11-28 03:00:00', 'backups/mongo/prd-mongo-tapo-aps-2/2024-11-28_02-03.zip', 's3://my-backup-bucket/backups/mongo/prd-mongo-tapo-aps-2/2024-11-28_02-03.zip'),
    ('mongo', 'prd-mongo-tapo-aps-3', '2024-11-28 03:00:00', '2024-11-28 04:00:00', 'backups/mongo/prd-mongo-tapo-aps-3/2024-11-28_03-04.zip', 's3://my-backup-bucket/backups/mongo/prd-mongo-tapo-aps-3/2024-11-28_03-04.zip'),
    ('mongo', 'prd-mongo-tapo-aps-4', '2024-11-28 04:00:00', '2024-11-28 05:00:00', 'backups/mongo/prd-mongo-tapo-aps-4/2024-11-28_04-05.zip', 's3://my-backup-bucket/backups/mongo/prd-mongo-tapo-aps-4/2024-11-28_04-05.zip'),
    ('mongo', 'prd-mongo-tapo-aps-5', '2024-11-28 05:00:00', '2024-11-28 06:00:00', 'backups/mongo/prd-mongo-tapo-aps-5/2024-11-28_05-06.zip', 's3://my-backup-bucket/backups/mongo/prd-mongo-tapo-aps-5/2024-11-28_05-06.zip'),
    ('mysql', 'prd-mysql-tapo-aps-6', '2024-11-28 06:00:00', '2024-11-28 07:00:00', 'backups/mysql/prd-mysql-tapo-aps-6/2024-11-28_06-07.zip', 's3://my-backup-bucket/backups/mysql/prd-mysql-tapo-aps-6/2024-11-28_06-07.zip'),
    ('mysql', 'prd-mysql-tapo-aps-7', '2024-11-28 07:00:00', '2024-11-28 08:00:00', 'backups/mysql/prd-mysql-tapo-aps-7/2024-11-28_07-08.zip', 's3://my-backup-bucket/backups/mysql/prd-mysql-tapo-aps-7/2024-11-28_07-08.zip'),
    ('mongo', 'prd-mongo-tapo-aps-6', '2024-11-28 06:00:00', '2024-11-28 07:00:00', 'backups/mongo/prd-mongo-tapo-aps-6/2024-11-28_06-07.zip', 's3://my-backup-bucket/backups/mongo/prd-mongo-tapo-aps-6/2024-11-28_06-07.zip'),
    ('mongo', 'prd-mongo-tapo-aps-7', '2024-11-28 07:00:00', '2024-11-28 08:00:00', 'backups/mongo/prd-mongo-tapo-aps-7/2024-11-28_07-08.zip', 's3://my-backup-bucket/backups/mongo/prd-mongo-tapo-aps-7/2024-11-28_07-08.zip'),
    ('mysql', 'prd-mysql-tapo-aps-8', '2024-11-28 08:00:00', '2024-11-28 09:00:00', 'backups/mysql/prd-mysql-tapo-aps-8/2024-11-28_08-09.zip', 's3://my-backup-bucket/backups/mysql/prd-mysql-tapo-aps-8/2024-11-28_08-09.zip');
