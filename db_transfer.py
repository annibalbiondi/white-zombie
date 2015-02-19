import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','poc_project.settings')
import pickle
import datetime
from reader.models import *

def retrieve_entries():
    entries = {}

    for feed in Feed.objects.all():
        entries[feed.address] = []

        for entry in Entry.objects.filter(feed=feed):
            title = entry.title
            description = entry.description
            link = entry.link
            pub_date = entry.pub_date.timetuple()
            entries[feed.address].append((title, description, link, pub_date))

    # executar pickle
    with open('entries', 'w') as storage_file:
        pickle.dump(entries, storage_file, 2)


def store_entries():
    entries = None

    with open('entries', 'r') as storage_file:
        entries = pickle.load(storage_file)

    for feed in Feed.objects.all():
        for entry in entries[feed.address]:
            e = Entry(feed=feed,
                      title=entry[0],
                      description=entry[1],
                      link=entry[2],
                      pub_date=datetime.datetime(entry[3][0],
                                                 entry[3][1],
                                                 entry[3][2],
                                                 entry[3][3],
                                                 entry[3][4],
                                                 entry[3][5]))
            e.save()

#retrieve_entries()
store_entries()
