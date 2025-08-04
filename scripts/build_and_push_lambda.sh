#!/bin/bash
# filepath: scripts/build_and_push_lambda.sh

# Read AWS parameters from config.yaml using Python
echo "Reading AWS configuration from config.yaml..."
ACCOUNT_ID="211125653762"
REGION="eu-west-2"
REPO_NAME="the-alchemiser-repository"
IMAGE_TAG=$(python -c "import yaml; print(yaml.safe_load(open('the_alchemiser/config.yaml'))['aws']['image_tag'])")
LAMBDA_ARN="arn:aws:lambda:eu-west-2:211125653762:function:the-alchemiser-lambda"

echo "Using AWS configuration: Account=${ACCOUNT_ID}, Region=${REGION}, Repo=${REPO_NAME}, Tag=${IMAGE_TAG}"

# Build the Docker image
echo "Building Docker image..."
DOCKER_BUILDKIT=0 docker build -t ${REPO_NAME} .

# Tag the image for ECR
echo "Tagging Docker image..."
docker tag ${REPO_NAME} ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}

# Authenticate Docker to ECR
echo "Authenticating to ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Push the image to ECR
echo "Pushing Docker image to ECR..."
docker push ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}

echo "Done! Image pushed to ECR."

# Update the Lambda function to use the new image
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"
echo "Updating Lambda function to use new image..."
aws lambda update-function-code --function-name "$LAMBDA_ARN" --image-uri "$IMAGE_URI" --region "$REGION" --no-cli-pager
echo "Lambda function updated."

# Delete all but the two most recent images in ECR
echo "Cleaning up old ECR images (keeping the two most recent)..."
old_digests=$(aws ecr describe-images --repository-name "$REPO_NAME" --region "$REGION" --output json | \
  jq -r '.imageDetails | sort_by(.imagePushedAt) | reverse | .[2:] | .[].imageDigest')

if [ -n "$old_digests" ]; then
  for digest in $old_digests; do
    echo "Deleting old image with digest: $digest"
    aws ecr batch-delete-image --repository-name "$REPO_NAME" --region "$REGION" --image-ids imageDigest="$digest" --no-cli-pager
  done
else
  echo "No old images to delete."
fi
echo "Old ECR images cleanup complete."

# Clean up local Docker disk usage
echo "Cleaning up local Docker disk usage..."
docker system prune -f
echo "Local Docker cleanup complete."
