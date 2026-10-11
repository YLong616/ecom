import sys
path = '/home/edisonyyl/dlt'
if path not in sys.path:
    sys.path.append(path)

from asgiref.wsgi import AsgiToWsgi
from app import app  # 假设app.py中有app对象

application = AsgiToWsgi(app)