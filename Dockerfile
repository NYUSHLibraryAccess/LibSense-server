# Use an official Python runtime as a parent image
FROM python:3.10

# Set environment variables
ENV ROOT_DIR="/home/libsense"
ENV APP_DIR="${ROOT_DIR}/LibSense-server"

# Set the working directory
WORKDIR $ROOT_DIR

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git && \
    rm -rf /var/lib/apt/lists/*

# Clone the repository
RUN git clone https://github.com/NYUSHLibraryAccess/LibSense-server.git $APP_DIR

# Set the working directory inside the cloned repository
WORKDIR $APP_DIR

# Checkout the main branch and reset to the latest commit
RUN git checkout main && git reset --hard HEAD && git pull

# Create necessary directories
RUN mkdir -p assets/to_del assets/source logs configs

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port FastAPI runs on
EXPOSE 8080

# Command to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
