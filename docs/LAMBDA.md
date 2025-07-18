# How to Update Your Docker Image, Push to ECR, and Update AWS Lambda

This guide walks you through updating your Docker image, pushing it to AWS ECR, and updating your Lambda function to use the new image.

---

## 1. Update Your Code and Docker Image

Make your code changes as needed. Then, rebuild your Docker image:

```sh
DOCKER_BUILDKIT=0 docker build -t lqq3-lambda .
```

## 2. Tag the Docker Image for ECR

Replace `<account-id>` and `<region>` with your AWS account ID and region (e.g., `211125653762` and `eu-west-2`).

```sh
docker tag lqq3-lambda <account-id>.dkr.ecr.<region>.amazonaws.com/lqq3-lambda:latest
```

Example:

```sh
docker tag lqq3-lambda 211125653762.dkr.ecr.eu-west-2.amazonaws.com/lqq3-lambda:latest
```

## 3. Authenticate Docker to ECR

```sh
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 211125653762.dkr.ecr.eu-west-2.amazonaws.com
```

## 4. Push the Image to ECR

```sh
docker push 211125653762.dkr.ecr.eu-west-2.amazonaws.com/lqq3-lambda:latest
```

## 5. Update Lambda to Use the New Image

1. Go to the AWS Lambda Console.
2. Select your Lambda function.
3. Under "Code", click "Edit" next to the image URI.
4. Enter the new image URI (e.g., `211125653762.dkr.ecr.eu-west-2.amazonaws.com/lqq3-lambda:latest`).
5. Click "Save".

---

## Notes

- Make sure your `.dockerignore` excludes sensitive files like `.env`.
- Always use the AWS Lambda base image (e.g., `public.ecr.aws/lambda/python:3.11`).
- If you get manifest/media type errors, rebuild with `DOCKER_BUILDKIT=0`.
- You can automate these steps with a shell script if desired.

---

## Troubleshooting

- If you get push access denied, make sure you have created the ECR repository and authenticated Docker.
- If Lambda can't use the image, check you are using the correct base image and manifest type.

---

**Reference this guide whenever you need to update your Lambda container image!**
