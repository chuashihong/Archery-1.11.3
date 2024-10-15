# Define variables for MySQL credentials and connection
$MYSQL_HOST = "127.0.0.1"            # MySQL host (adjust as needed)
$MYSQL_PORT = "3307"                 # Local machine port mapped to Docker MySQL
$MYSQL_USER = "root"                 # MySQL username
$MYSQL_PASSWORD = "password123"           # MySQL password
$SQL_FILE = "data-insertion.sql"     # Path to your SQL file

# Check if the SQL file exists
if (-not (Test-Path $SQL_FILE)) {
    Write-Host "SQL file '$SQL_FILE' not found. Please ensure the file exists in the script directory."
    exit 1
}

# Build the MySQL command to execute the SQL file
$mysqlCommand = "mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD < $SQL_FILE"

# Display the command for confirmation
Write-Host "Executing the following MySQL command:"
Write-Host $mysqlCommand

# Run the MySQL command using `cmd` since PowerShell's `&` operator doesn't handle "<" (file redirection) correctly
cmd /c $mysqlCommand

# Check if the command executed successfully
if ($LASTEXITCODE -eq 0) {
    Write-Host "SQL script executed successfully!"
} else {
    Write-Host "Failed to execute SQL script."
}
