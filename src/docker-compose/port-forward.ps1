Write-Host "SCRIPT LOG: Port forwarding"
# Port forward the MySQL service and MongoDB service to localhost
# Start-Process kubectl -ArgumentList "port-forward deployment/mysql 3307:3306"
# Start-Process kubectl -ArgumentList "port-forward deployment/mongodb 27018:27017"
# Start-Process kubectl -ArgumentList "port-forward service/db-1-service 3308:3306"
# Start-Process kubectl -ArgumentList "port-forward service/db-2-service 3309:3306"
# Start-Process kubectl -ArgumentList "port-forward service/db-3-service 27017:27017"
# Start-Process kubectl -ArgumentList "port-forward service/db-4-service 27018:27017"


Start-Process kubectl -ArgumentList "port-forward service/log-db-service 3308:3306"
Start-Process kubectl -ArgumentList "port-forward service/mysql-instance-service 3309:3306"
Start-Process kubectl -ArgumentList "port-forward service/minio 9000:9000"
Start-Process kubectl -ArgumentList "port-forward service/minio 46095:46095"