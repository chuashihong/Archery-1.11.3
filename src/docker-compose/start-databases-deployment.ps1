# PowerShell script to apply multiple Kubernetes YAML files at once and start Archer container on Docker
# Start minikube for kubernetes cluster
minikube start
# Run the docker-compose up command to start the deployment
docker-compose -f .\docker-compose.yml up -d
# Navigate to the directory containing the YAML files
cd "C:\Users\shihong.chua\playground\ArcheryVersion\Archery-1.11.3\src\docker-compose"
Write-Host "SCRIPT LOG: Applying new deployments and services..."
# Apply the MongoDB and MySQL deployments and services
kubectl apply -f .\k8s\mongo-deployment.yml
kubectl apply -f .\k8s\mongo-service.yml
kubectl apply -f .\k8s\mysql-configmap.yml
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
Write-Host "SCRIPT LOG: Port forwarding in 3 seconds..."
# Print the countdown message for port forwarding
for ($i = 1; $i -le 3; $i++) {
    Write-Host "SCRIPT LOG: Port forwarding in $(4 - $i) seconds..."
    Start-Sleep -Seconds 1
}
Write-Host "SCRIPT LOG: Port forwarding from 3307 to 3306 and 27018 to 27017..."
# Port forward the MySQL service and MongoDB service to localhost
Start-Process kubectl -ArgumentList "port-forward deployment/mysql 3307:3306"
Start-Process kubectl -ArgumentList "port-forward deployment/mongodb 27018:27017"
