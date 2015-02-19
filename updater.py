import os
#os.environ.setdefault('DJANGO_SETTINGS_MODULE','poc_project.settings')
from reader import rss

rss.update_feeds()
