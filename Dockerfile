# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install C compiler and other build tools
RUN apt-get update && apt-get install -y build-essential

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Environment variable for the Hugging Face token
# This will be passed in from the docker-compose.yml file
ARG HUGGING_FACE_TOKEN
ENV HUGGING_FACE_TOKEN=$HUGGING_FACE_TOKEN

# Run the authentication script during the build
RUN python authenticate_hf.py

# Make the run script executable
RUN chmod +x ./run.sh

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run run.sh when the container launches
CMD ["./run.sh"] 