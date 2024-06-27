# Use an official Python runtime as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the working directory
COPY . .

# Expose the port on which the app will run (default is 8000 for FastAPI)
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "converter:app", "--host", "0.0.0.0", "--port", "8000"]
