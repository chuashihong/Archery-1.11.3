# Configuration
$hostname = "localhost"
$port = 3309
$username = "root"
$password = "chuashihong"

# Tables and corresponding databases
$tables = @(
    @{db="db1"; table="table1"},
    @{db="db1"; table="table2"},
    @{db="db2"; table="table3"},
    @{db="db2"; table="table4"}
)

# Initialize a counter
$counter = 1

# Function to insert a row into a table
function Insert-IntoTable {
    param (
        [string]$database,
        [string]$table,
        [int]$value
    )
    
    # MySQL insert command
    $query = "INSERT INTO $table (value) VALUES ($value);"
    
    # Execute the command
    & mysql --host=$hostname --port=$port --user=$username --password=$password --database=$database --execute=$query
}

# Cycle through the tables
while ($true) {
    foreach ($entry in $tables) {
        $db = $entry.db
        $table = $entry.table

        Write-Host "Inserting into $db.$table with value $counter at $(Get-Date)"
        Insert-IntoTable -database $db -table $table -value $counter

        # Increment the counter
        $counter++

        # Wait for 3 seconds before the next table
        Start-Sleep -Seconds 3
    }
}
