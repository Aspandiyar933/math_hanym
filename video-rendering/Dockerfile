# Use the official Python image as the base image
FROM python:3.9-slim

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    manim \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create and change to the app directory
WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the application port
EXPOSE 5000

# Run the application
CMD ["python", "subscriber.py"]
