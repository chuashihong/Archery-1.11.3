# PowerShell script to apply multiple Kubernetes YAML files at once

# Run the docker-compose up command to start the deployment
docker-compose -f .\docker-compose.yml up -d

# Navigate to the directory containing the YAML files
cd "C:\Users\shihong.chua\playground\ArcheryVersion\Archery-1.11.3\src\docker-compose"

Write-Host "SCRIPT LOG: Deleting existing deployments and services..."
# Delete the MongoDB and MySQL deployments and services
kubectl delete -f .\k8s\mongo-deployment.yml
kubectl delete -f .\k8s\mongo-service.yml
kubectl delete -f .\k8s\mysql-deployment.yml
kubectl delete -f .\k8s\mysql-service.yml

Write-Host "SCRIPT LOG: Applying new deployments and services..."

# Apply the MongoDB and MySQL deployments and services
kubectl apply -f .\k8s\mongo-deployment.yml
kubectl apply -f .\k8s\mongo-service.yml
kubectl apply -f .\k8s\mysql-deployment.yml
kubectl apply -f .\k8s\mysql-service.yml

Write-Host "SCRIPT LOG: Deployment completed."

# # Print the message for waiting
Write-Host "SCRIPT LOG: Waiting for 5 seconds before port forwarding..."
# Print every (5 - i) seconds to indicate the waiting time
for ($i = 1; $i -le 5; $i++) {
    Write-Host "SCRIPT LOG: Remaining time: $(5 - $i) seconds"
    Start-Sleep -Seconds 1
}

# Write-Host "SCRIPT LOG: Port forwarding..."
# # Port forward the MySQL service and MongoDB service to localhost
# Start-Process kubectl -ArgumentList "port-forward deployment/mysql 3307:3306"
# Start-Process kubectl -ArgumentList "port-forward deployment/mongodb 27018:27017"
# kubectl port-forward pod/$(kubectl get pods -l app=mysql -o jsonpath='{.items[0].metadata.name}') 3307:3307
# kubectl port-forward pod/$(kubectl get pods -l app=mongodb -o jsonpath='{.items[0].metadata.name}') 27017:27017

# Connect to the MySQL database and MongoDB database
### Original command in bash
# mysql -P 3307 -u root -ppassword123
# mongosh --port 27018 -u admin -p password123
### Convert to PowerShell
# Open a new PowerShell window and run the following commands without closing the current window
# Start-Process powershell -ArgumentList "-NoExit -Command mysql -P 3307 -u root -ppassword123"
# Start-Process powershell -ArgumentList "-NoExit -Command mongosh --port 27018 -u admin -p password123"
# Start-Process mysql -ArgumentList "-P 3307 -u root -ppassword123"
# Start-Process mongosh -ArgumentList "--port 27018 -u admin -p password123"