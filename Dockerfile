# Use Oracle Linux 8 Slim as the base image
FROM container-registry.oracle.com/os/oraclelinux:8-slim

# Install necessary packages and oci-cli
RUN set -ex \
    && microdnf update -y \
    && microdnf install -y python39 python39-pip git curl unzip zip\
    && microdnf clean all \
    \
    # Install OCI CLI using Oracle's installer
    && curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh \
        | bash -s -- --accept-all-defaults --install-dir /usr/local/lib/oci-cli \
    \
    # Symlink oci to a location in PATH
    && ln -s /usr/local/lib/oci-cli/bin/oci /usr/local/bin/oci

WORKDIR /app
COPY . /app

ENV PATH="/usr/local/lib/oci-cli/bin:$PATH"