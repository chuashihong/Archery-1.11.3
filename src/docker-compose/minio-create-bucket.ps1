# Define Variables
$podName = (kubectl get pods -l app=minio -o jsonpath="{.items[0].metadata.name}")
$bucketName = "backups"
$minioEndpoint = "http://127.0.0.1:9000"
$accessKey = "chuashihong"
$secretKey = "chuashihong"

# Display the Pod Name
Write-Host "Using MinIO Pod: $podName"

# Configure MinIO Client (mc) and Create Bucket
kubectl exec -it $podName -- /bin/sh -c @"
if ! command -v mc > /dev/null; then
  wget https://dl.min.io/client/mc/release/linux-amd64/mc -O /usr/bin/mc && \
  chmod +x /usr/bin/mc
fi && \
mc alias set myminio $minioEndpoint $accessKey $secretKey && \
mc mb myminio/$bucketName
"@

# Verify Bucket Creation
Write-Host "Verifying bucket creation..."
kubectl exec -it $podName -- /bin/sh -c "mc ls myminio"
