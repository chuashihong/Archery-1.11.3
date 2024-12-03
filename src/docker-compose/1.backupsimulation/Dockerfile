FROM python:3.10-slim

WORKDIR /scripts

# Install required system tools and Python dependencies
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    zip && \
    pip install pymysql

# # Copy the Python script
# COPY mysql_increment.py /scripts/

# # Set the default command
# CMD ["python", "/scripts/mysql_increment.py"]
