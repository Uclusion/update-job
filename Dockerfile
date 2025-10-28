FROM ubuntu:latest

COPY entrypoint.sh /entrypoint.py

# Define the entrypoint for the action
ENTRYPOINT ["/entrypoint.py"]