# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 8888

# Define environment variable
ENV NAME TOPIC

# Run app_local.py when the container launches
# CMD ["python", "app_topic_gpt35.py"]
CMD ["python", "app_topic_gpt35.py"]