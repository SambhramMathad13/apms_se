import logging
from waitress import serve
from aps.wsgi import application  # replace with your actual project name

# Configure logging
logging.basicConfig(
    filename="logs.txt",  # Log file name
    level=logging.INFO,   # Log level
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Run the server
serve(application, host='0.0.0.0', port=8000)