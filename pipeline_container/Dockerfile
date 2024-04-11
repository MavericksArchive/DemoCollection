# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn gevent

# Make port 80 available to the world outside this container
EXPOSE 2222

# Define environment variable
ENV NAME INTENTION

# Run app.py when the container launches
# CMD ["python", "Papyrus_release_v4.py"]
CMD ["gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:2222", "Papyrus_release_v4:app"] 
