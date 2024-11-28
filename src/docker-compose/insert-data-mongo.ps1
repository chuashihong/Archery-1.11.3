# Define MongoDB connection details
$MONGO_HOST = "127.0.0.1"
$MONGO_PORT = "27018"                         # MongoDB port
$MONGO_USER = "admin"                         # MongoDB username
$MONGO_PASSWORD = "password123"               # MongoDB password
$AUTH_DB = "admin"                            # Authentication database
$JSON_FILE = "mongo_test_data.json" #  JSON file containing data for multiple databases and collections

# Check if the JSON file exists
if (-not (Test-Path $JSON_FILE)) {
    Write-Host "Data file '$JSON_FILE' not found. Please ensure it exists."
    exit 1
}

# Load JSON data
$data = Get-Content -Raw -Path $JSON_FILE | ConvertFrom-Json

# Loop through each database and collection in the JSON data
foreach ($dbName in $data.PSObject.Properties.Name) {
    $dbData = $data.$dbName
    foreach ($collectionName in $dbData.PSObject.Properties.Name) {
        $documents = $dbData.$collectionName

        # Create a temporary JSON file for the collection
        $tempFilePath = "$PSScriptRoot\$dbName`_$collectionName.json"
        $documents | ConvertTo-Json -Compress | Set-Content -Path $tempFilePath

        # Build and run the mongoimport command with authentication
        $mongoCommand = "mongoimport --host $MONGO_HOST --port $MONGO_PORT --username $MONGO_USER --password $MONGO_PASSWORD --authenticationDatabase $AUTH_DB --db $dbName --collection $collectionName --file `"$tempFilePath`" --jsonArray"
        
        Write-Host "Importing data into $dbName.$collectionName..."
        cmd /c $mongoCommand

        # Check if the import was successful
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Data imported successfully into $dbName.$collectionName!"
        } else {
            Write-Host "Failed to import data into $dbName.$collectionName."
        }

        # Clean up the temporary file
        Remove-Item -Path $tempFilePath
    }
}