#!/bin/bash
set -e

echo "Downloading Oracle Instant Client..."
mkdir -p /opt/oracle
cd /opt/oracle

# Download Basic Lite package for Linux x64
wget -q https://download.oracle.com/otn_software/linux/instantclient/2115000/instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip

echo "Installing unzip..."
# Render uses apt by default for web services
apt-get update && apt-get install -y unzip libaio1

echo "Unzipping Instant Client..."
unzip -q instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip
rm instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip

echo "Configuring environment..."
sh -c "echo /opt/oracle/instantclient_21_15 > /etc/ld.so.conf.d/oracle-instantclient.conf"
ldconfig

echo "Oracle Instant Client installed successfully."
