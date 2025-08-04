# Use the official Python image
FROM python:3.9-slim

# Set the environment variable for SaxonC
ENV SAXONC_HOME=/opt/SaxonC

# Install required packages (like wget and unzip for SaxonC)
RUN apt-get update && apt-get install -y \
    wget \
    unzip

# Download and install SaxonC-HE for Linux
RUN wget https://downloads.saxonica.com/SaxonC/HE/12/libsaxon-HEC-linux-x86_64-v12.5.0.zip -O saxonc.zip && \
    unzip saxonc.zip -d /opt && \
    rm saxonc.zip

# Install the Python dependencies for the backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code into the container
COPY . /app
WORKDIR /app

# Expose the port the Flask app will run on
EXPOSE 3000

# Run the Flask app
CMD ["python", "backend.py"]

