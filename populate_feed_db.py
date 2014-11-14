import datetime
import feedparser
import locale
import os
import re
from dateutil.parser import parse
from django.utils import timezone

global user

users = [
    {
        'username': 'test_user',
        'password': 'password'
        }
    ]

feeds = [
    'http://rss.uol.com.br/feed/noticias.xml',
    ]

def populate():
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    for x in feeds:
        d = feedparser.parse(x)
        feed = add_feed(d.feed.title, d.feed.link, d.feed.description)
        for e in d.entries:
            add_entry(e.title, e.link, e.description, e.published, feed)

    for u in users:
        user = add_user(u['username'], u['password'])
        for f in Feed.objects.all():
            user.feeds.add(f)
            for e in Entry.objects.filter(feed=f):
                received_entry = ReceivedEntry.objects.get_or_create(
                    entry=e)[0]
                user.entries_received.add(received_entry)

                print "- {0} - {1}".format(str(f), str(e))
        user.save()


def add_feed(title, link, description):
    f = Feed.objects.get_or_create(
        title=title,
        link=link,
        description=description
        )[0]
    return f


def add_entry(title, link, description, pub_date, feed):
    pub_date = pub_date.encode('utf-8')
    pub_date = re.match(r'(.*)\s(\+|-)', pub_date, re.LOCALE | re.UNICODE).group(1)
    print pub_date
    e = Entry.objects.get_or_create(
        title=title,
        link=link,
        description=description,
        # TODO inserir fuso-horario
        pub_date=datetime.datetime.strptime(
            pub_date, '%a, %d %b %Y %H:%M:%S'),
        feed=feed)[0]
    return e


def add_user(username, password):
    user = User.objects.get_or_create(
        username=username,
        password=password,
        is_staff=False,
        is_active=True,
        is_superuser=False)[0]
    user.set_password(user.password)
    user.save()
    u = ReaderUser.objects.get_or_create(
        user=user)[0]

    return u


if __name__ == '__main__':
    print 'Populating database...'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','poc_project.settings')
    from reader.models import Feed, Entry, ReaderUser, ReceivedEntry
    from django.contrib.auth.models import User
    populate()
