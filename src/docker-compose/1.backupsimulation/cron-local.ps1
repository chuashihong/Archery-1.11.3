# Path to Python script
$ScriptPath = "incremental_backup.py"

while ($true) {
    # Run the Python script
    & python3 $ScriptPath

    # Wait for 60 seconds before running again
    Start-Sleep -Seconds 60
}
