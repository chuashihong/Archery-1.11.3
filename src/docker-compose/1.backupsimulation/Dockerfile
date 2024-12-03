FROM python:3.10-slim

WORKDIR /scripts

# Install required system tools and Python dependencies
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    zip && \
    pip install --upgrade pip && \
    pip install pymysql boto3

# Expose the working directory
VOLUME /scripts

# Ensure entrypoint remains flexible for mounting and running scripts
ENTRYPOINT ["/bin/bash"]
