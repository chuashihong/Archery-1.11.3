# PowerShell script to apply multiple Kubernetes YAML files at once and start Archer container on Docker
# Start minikube for kubernetes cluster

# kubectl apply -f .\k8s\another-mongo.yml
# kubectl apply -f .\k8s\another-mysql.yml
# kubectl apply -f .\k8s\mongo-deployment.yml
# kubectl apply -f .\k8s\mongo-service.yml
# kubectl apply -f .\k8s\mysql-configmap.yml
# kubectl apply -f .\k8s\mysql-deployment.yml
# kubectl apply -f .\k8s\mysql-service.yml
# kubectl apply -f .\k8s\mysql-backup-data.yml
# kubectl apply -f .\k8s\mysql-backup-data-service.yml



kubectl apply -f .\k8s\db-1-deployment.yml
kubectl apply -f .\k8s\db-2-deployment.yml
kubectl apply -f .\k8s\db-3-deployment.yml
kubectl apply -f .\k8s\db-4-deployment.yml

