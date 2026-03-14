# Use official Python 3.10 slim image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    libaio1 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Oracle Instant Client 21c Basic Lite
WORKDIR /opt/oracle
RUN wget -q https://download.oracle.com/otn_software/linux/instantclient/2115000/instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip \
    && unzip -q instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip \
    && rm instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip

# Configure dynamic linker run-time bindings
RUN echo "/opt/oracle/instantclient_21_15" > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# Set app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose SSE port (dynamic via $PORT on Render, defaulting to 8120)
ENV PORT=8120
EXPOSE 8120

# Start MCP Server
CMD ["python", "tutorial_procurement_mcp_server.py", "--sse"]
