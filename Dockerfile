# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install uv
RUN pip install uv

# Copy the project files into the container
COPY . .

# Install dependencies using uv
RUN uv pip sync pyproject.toml

# Set environment variables for non-interactive installations
ENV DEBIAN_FRONTEND=noninteractive

# Environment variable for the Hugging Face token
# This will be passed in from the docker-compose.yml file
ARG HUGGING_FACE_TOKEN
ENV HUGGING_FACE_TOKEN=$HUGGING_FACE_TOKEN

# Run the authentication script
RUN --mount=type=cache,target=/root/.cache/huggingface \
    python authenticate_hf.py

# Make the run script executable
RUN chmod +x ./run.sh

# The command to run the application
CMD ["./run.sh"] 