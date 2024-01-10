import sys, os
cwd = os.getcwd()
sys.path.append(cwd)
sys.path.append(cwd + '/morgan_ai')

INTERP = os.path.expanduser("~/django.ferree-gering.com/.venv/bin/python")

if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0,'/home/ferreegering/django.ferree-gering.com/.venv/bin')
#sys.path.insert(0,'/home/ferreegering/django.ferree-gering.com/.venv/lib/python3.9/site-packages/django')
sys.path.insert(0,'/home/ferreegering/django.ferree-gering.com/.venv/lib/python3.9/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = "morgan_ai.settings"
from morgan_proj.wsgi import application
#from django.core.wsgi import get_wsgi_application
#application = get_wsgi_application()
