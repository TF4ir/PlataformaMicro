#!/usr/bin/env bash
# ==============================================================================
# Build and push the FastAPI Lambda image to Amazon ECR.
#
# Prerequisites:
#   - AWS CLI v2 authenticated with permissions for ECR.
#   - Docker with linux/amd64 support.
#   - The ECR stack (deploy/aws/ecr.yaml) already deployed, or permissions to
#     create the repository on demand.
#
# Usage:
#   AWS_REGION=us-east-2 IMAGE_TAG=mvp-$(git rev-parse --short HEAD) \
#     deploy/aws/build_and_push.sh
#
# The script prints the exact ImageUri to pass to `sam deploy`.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

AWS_REGION="${AWS_REGION:-us-east-2}"
ECR_REPO_NAME="${ECR_REPO_NAME:-nexo-mvp-ml-api}"
IMAGE_TAG="${IMAGE_TAG:-mvp-$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"
PLATFORM="${PLATFORM:-linux/amd64}"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
FULL_IMAGE_URI="${ECR_URI}:${IMAGE_TAG}"

if ! aws ecr describe-repositories --region "${AWS_REGION}" \
  --repository-names "${ECR_REPO_NAME}" >/dev/null 2>&1; then
  echo "ERROR: ECR repository ${ECR_REPO_NAME} does not exist in region ${AWS_REGION}."
  echo "Deploy the repository first with CloudFormation using deploy/aws/ecr.yaml:"
  echo "  sam deploy --template-file deploy/aws/ecr.yaml --stack-name nexo-mvp-ecr --region ${AWS_REGION}"
  exit 1
fi

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Ensure single-architecture linux/amd64 image manifest is created (never multi-architecture OCI index or provenance/SBOM attestations)
if docker buildx version >/dev/null 2>&1; then
  echo "Building ${FULL_IMAGE_URI} for ${PLATFORM} using buildx (single-architecture, provenance and sbom disabled)..."
  docker buildx build \
    --platform "${PLATFORM}" \
    --provenance=false \
    --sbom=false \
    --file "${REPO_ROOT}/services/ml-api/Dockerfile.lambda" \
    --tag "${FULL_IMAGE_URI}" \
    --load \
    "${REPO_ROOT}"
else
  echo "Building ${FULL_IMAGE_URI} for ${PLATFORM} using standard docker build..."
  docker build \
    --platform "${PLATFORM}" \
    --file "${REPO_ROOT}/services/ml-api/Dockerfile.lambda" \
    --tag "${FULL_IMAGE_URI}" \
    "${REPO_ROOT}"
fi

docker push "${FULL_IMAGE_URI}"

cat <<EOF

Image pushed successfully.

Use this value for the SAM ImageUri parameter:
  ImageUri=${FULL_IMAGE_URI}

Example deployment command (with CloudFormation Execution Role):
  sam deploy \\
    --template-file deploy/aws/template.yaml \\
    --stack-name nexo-mvp-ml-api \\
    --region ${AWS_REGION} \\
    --capabilities CAPABILITY_NAMED_IAM \\
    --role-arn arn:aws:iam::${ACCOUNT_ID}:role/nexo-mvp-cloudformation-role \\
    --parameter-overrides \\
      ImageUri=${FULL_IMAGE_URI} \\
      DatabaseSecretArn='arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:nexo-mvp-database-dsn-xxxxxx'

Example deployment command (direct operator deployment):
  sam deploy \\
    --template-file deploy/aws/template.yaml \\
    --stack-name nexo-mvp-ml-api \\
    --region ${AWS_REGION} \\
    --capabilities CAPABILITY_NAMED_IAM \\
    --parameter-overrides \\
      ImageUri=${FULL_IMAGE_URI} \\
      DatabaseSecretArn='arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:nexo-mvp-database-dsn-xxxxxx'

EOF
