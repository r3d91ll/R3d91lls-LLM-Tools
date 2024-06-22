#!/bin/bash

# Set the number of cores devoted to building the base image
MAX_JOBS=36

# Record the start time
start_time=$(date +%s)

# Build the base image without creating a container
docker build --no-cache -t myllm-base:latest -f Dockerfile.base \
    --build-arg MAX_JOBS=$MAX_JOBS \
    --cpuset-cpus="0-35" \
    --memory=200g .

# Check if the build was successful
if [ $? -eq 0 ]; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    echo "Base image built successfully in $duration seconds"
    echo "That's approximately $((duration / 60)) minutes and $((duration % 60)) seconds"
else
    echo "Failed to build base image"
    exit 1
fi