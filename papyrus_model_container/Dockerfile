# Use an official Python runtime as a parent image
# FROM huggingface/optimum-nvidia
FROM python:3.10-slim
#FROM 3.10-slim-bullseye
# FROM 3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

RUN apt-get update && apt-get install -y git build-essential

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install xformers --index-url https://download.pytorch.org/whl/cu121
RUN pip install "unsloth[cu121-torch220] @ git+https://github.com/unslothai/unsloth.git"
RUN pip install gunicorn gevent


# Make port 80 available to the world outside this container
EXPOSE 8090

# Define environment variable
ENV NAME PAPYRUSOPT

# Run app.py when the container launches
# CMD ["python", "app.py"]
CMD ["gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:8090", "app:app"] 

