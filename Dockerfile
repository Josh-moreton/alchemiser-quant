# Dockerfile for Nuclear Trading Bot (AWS Lambda Container)
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for numba/llvmlite
RUN yum install -y gcc llvm-devel

# Copy source code
COPY . /var/task

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Lambda handler
CMD ["lambda_handler.lambda_handler"]
