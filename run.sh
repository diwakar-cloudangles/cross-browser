# run.sh
#!/bin/bash

# Start MySQL container


# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."


# Install Python dependencies
# pip install -r requirements.txt

# Start the FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload