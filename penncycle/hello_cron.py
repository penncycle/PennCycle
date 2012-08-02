import os
from os.path import abspath, dirname
import sys
path = '~/penncycle'
if path not in sys.path:
    sys.path.append(path)
sys.path.insert(0, path)
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

from app.models import *
from app.views import email_alex

students = Student.objects.all()
message = '\n'.join([s.name for s in students])

email_alex(message)