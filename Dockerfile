FROM ubuntu:latest

COPY entrypoint.py /usr/local/bin/entrypoint.py

# Make the entrypoint.py executable
RUN chmod +x /usr/local/bin/entrypoint.py

# Set the entrypoint for your container
ENTRYPOINT ["/usr/local/bin/entrypoint.py"]