#!/bin/bash
# Setup MinIO buckets and initial configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# MinIO configuration
MINIO_ENDPOINT="${MINIO_ENDPOINT:-localhost:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin}"
MINIO_SECURE="${MINIO_SECURE:-false}"

echo "=========================================="
echo "Setting up MinIO Storage"
echo "=========================================="
echo ""

# Check if MinIO client (mc) is installed
if ! command -v mc &> /dev/null; then
    echo "MinIO client (mc) not found. Installing..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        wget https://dl.min.io/client/mc/release/linux-amd64/mc -O /tmp/mc
        chmod +x /tmp/mc
        sudo mv /tmp/mc /usr/local/bin/
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install minio/stable/mc
    else
        echo "Please install MinIO client manually: https://min.io/docs/minio/linux/reference/minio-mc.html"
        exit 1
    fi
    
    echo "✓ MinIO client installed"
fi

# Configure MinIO client
echo "Configuring MinIO client..."
mc alias set local http://$MINIO_ENDPOINT $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
max_attempts=30
attempt=0
while ! mc admin info local &> /dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "❌ MinIO is not responding after $max_attempts attempts"
        echo "Please ensure MinIO is running:"
        echo "  docker-compose up -d minio"
        exit 1
    fi
    echo "  Attempt $attempt/$max_attempts..."
    sleep 2
done

echo "✓ MinIO is ready"
echo ""

# Create buckets
echo "Creating buckets..."

buckets=(
    "3d-pipeline"
)

for bucket in "${buckets[@]}"; do
    if mc ls local/$bucket &> /dev/null; then
        echo "  ✓ Bucket '$bucket' already exists"
    else
        mc mb local/$bucket
        echo "  ✓ Created bucket '$bucket'"
    fi
done

echo ""

# Create folder structure in main bucket
echo "Creating folder structure..."

folders=(
    "3d-pipeline/uploads"
    "3d-pipeline/frames"
    "3d-pipeline/sparse"
    "3d-pipeline/dense"
    "3d-pipeline/ai"
    "3d-pipeline/splats"
    "3d-pipeline/meshes"
    "3d-pipeline/physics"
    "3d-pipeline/exports"
)

for folder in "${folders[@]}"; do
    # Create a placeholder file to ensure folder exists
    echo "" | mc pipe local/$folder/.gitkeep
    echo "  ✓ Created folder '$folder'"
done

echo ""

# Set bucket policies (public read for exports)
echo "Setting bucket policies..."
cat > /tmp/policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::3d-pipeline/exports/*"]
    }
  ]
}
EOF

mc anonymous set-json /tmp/policy.json local/3d-pipeline
rm /tmp/policy.json

echo "✓ Bucket policies configured"
echo ""

# Display bucket info
echo "=========================================="
echo "MinIO Setup Complete!"
echo "=========================================="
echo ""
echo "Endpoint: http://$MINIO_ENDPOINT"
echo "Console: http://localhost:9001"
echo "Access Key: $MINIO_ACCESS_KEY"
echo "Secret Key: $MINIO_SECRET_KEY"
echo ""
echo "Buckets created:"
for bucket in "${buckets[@]}"; do
    echo "  - $bucket"
done
echo ""
echo "Folder structure:"
for folder in "${folders[@]}"; do
    echo "  - $folder"
done
echo ""
echo "You can access the MinIO console at: http://localhost:9001"
echo "Login with the access key and secret key above."
