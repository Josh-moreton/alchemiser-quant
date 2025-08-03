# Use the official AWS Lambda Python runtime as base image
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements file
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install poetry

# Configure Poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only=main --no-dev

# Copy function code
COPY the_alchemiser/ ${LAMBDA_TASK_ROOT}/the_alchemiser/

# Set the CMD to your handler
CMD ["the_alchemiser.lambda_handler.lambda_handler"]
