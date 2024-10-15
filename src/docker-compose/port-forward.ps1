Write-Host "SCRIPT LOG: Port forwarding from 3307 to 3306 and 27018 to 27017..."
# Port forward the MySQL service and MongoDB service to localhost
Start-Process kubectl -ArgumentList "port-forward deployment/mysql 3307:3306"
Start-Process kubectl -ArgumentList "port-forward deployment/mongodb 27018:27017"
