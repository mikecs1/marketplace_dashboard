import sys
import os

# Add your project directory to the path
project_home = '/home/yourusername/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_APP'] = 'app.py'

# Import and run the app
from app import app as application
