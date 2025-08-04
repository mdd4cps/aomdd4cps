# Use the official Python image
FROM python:3.9-slim

# Install the Python dependencies for the frontend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the frontend code into the container
COPY . /app
WORKDIR /app

# Expose the port the Flask frontend will run on
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
