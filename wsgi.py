import sys
import os

project_home = '/home/yourusername/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['FLASK_APP'] = 'app.py'

from app import app as application
