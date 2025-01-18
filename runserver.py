from waitress import serve
from aps.wsgi import application  # replace with your actual project name

serve(application, host='0.0.0.0', port=8000)