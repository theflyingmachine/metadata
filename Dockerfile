# Use Oracle Linux 8 Slim as the base image
FROM container-registry.oracle.com/os/oraclelinux:8-slim

# Install necessary packages
RUN set -ex \
    && microdnf update -y \
    && microdnf install -y python39 python39-pip git \
    && microdnf clean all

# Set the working directory inside the container
WORKDIR /app

# Copy all files from the current directory on the host to the /app directory in the container
COPY . /app

# Command to validate JSON files
CMD ["python3", "validate_json.py"]