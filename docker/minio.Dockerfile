# MinIO Object Storage Dockerfile
FROM minio/minio:latest

# Set environment variables
ENV MINIO_ROOT_USER=minioadmin
ENV MINIO_ROOT_PASSWORD=minioadmin
ENV MINIO_DOMAIN=localhost

# Create data directory
RUN mkdir -p /data

# Expose ports
EXPOSE 9000 9001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:9000/minio/health/live || exit 1

# Start MinIO server
CMD ["server", "/data", "--console-address", ":9001"]
