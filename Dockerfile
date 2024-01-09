# Use an Ubuntu base image with NVIDIA GPU support
FROM nvidia/cuda:11.3.1-base-ubuntu20.04

# Set environment variable to avoid interactive prompts
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    sudo \
    build-essential \
    python3.8 \
    python3.8-dev \
    python3-pip \
    ninja-build \
    ffmpeg \
    libsm6 \
    libxext6 \
    # Add other required packages here
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set CUDA_HOME environment variable
ENV CUDA_HOME=/usr/local/cuda

# Create a working directory
WORKDIR /app

# Copy the install_requirements.sh script
COPY install_requirements.sh .

# Run the script to install additional requirements
RUN chmod +x install_requirements.sh && ./install_requirements.sh

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install torch==1.8.1+cu111 torchvision==0.9.1+cu111 torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html

# Copy the application code into the container
COPY ./app .

# Expose the desired port (if your application listens on a specific port)
EXPOSE 8002

# Set the default command to run your application
CMD ["python3.8", "./tracking/app.py"]

