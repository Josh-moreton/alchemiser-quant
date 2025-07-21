#!/bin/bash
# filepath: scripts/build_and_push_lambda.sh

# Set these variables for your AWS account and region
ACCOUNT_ID=211125653762
REGION=eu-west-2
REPO_NAME=lqq3-lambda
IMAGE_TAG=latest

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