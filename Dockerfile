# Dockerfile for Nuclear Trading Bot (AWS Lambda Container)
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for numba/llvmlite
RUN yum install -y gcc llvm-devel

# Copy project source code
COPY the_alchemiser/ /var/task/the_alchemiser/
COPY scripts/ /var/task/scripts/
COPY config.yaml requirements.txt /var/task/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Lambda handler
CMD ["the_alchemiser.lambda_handler.lambda_handler"]
