# PowerShell script to apply multiple Kubernetes YAML files at once and start Archer container on Docker
# Start minikube for kubernetes cluster
Write-Host "SCRIPT LOG: Running docker-compose up command..."
docker-compose -f .\docker-compose.yml up -d
# Run the docker-compose up command to start the deployment
# Navigate to the directory containing the YAML files
# cd "C:\Users\shihong.chua\playground\ArcheryVersion\Archery-1.11.3\src\docker-compose"
Write-Host "SCRIPT LOG: Applying new deployments and services..."
# Apply the MongoDB and MySQL deployments and services
# kubectl apply -f .\k8s\db-1-deployment.yml
# kubectl apply -f .\k8s\db-2-deployment.yml
# kubectl apply -f .\k8s\db-3-deployment.yml
# kubectl apply -f .\k8s\db-4-deployment.yml
kubectl apply -f ./1.backupsimulation/cronjob.yaml
# kubectl apply -f ./1.backupsimulation/cronjob-inc.yaml
kubectl apply -f ./1.backupsimulation/db.yaml
kubectl apply -f ./1.backupsimulation/minio.yaml
Write-Host "SCRIPT LOG: Deployment completed."
