FROM ubuntu:latest

COPY entrypoint.py /entrypoint.py

# Define the entrypoint for the action
ENTRYPOINT ["/entrypoint.py"]