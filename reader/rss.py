# coding=utf-8
import re
import datetime
import feedparser
from reader.models import Feed, Entry, ReaderUser, ReceivedEntry

def fetch_feed(url):
    d = feedparser.parse(url)
    title = d.feed.get('title', 'no title')
    link = d.feed.get('link', 'http://nolink')
    description = d.feed.get('description', 'no description')
    language = d.feed.get('language')
    copyright_notice = d.feed.get('rights_detail', {}).get('value')
    managing_editor = d.feed.get('author_detail', {}).get('email')
    webmaster = d.feed.get('publisher_detail', {}).get('email')
    parsed_pub_date = d.feed.get('published_parsed')
    if (parsed_pub_date != None):
        pub_date = datetime.datetime(
            parsed_pub_date['tm_year'],
            parsed_pub_date['tm_mon'],
            parsed_pub_date['tm_day'],
            parsed_pub_date['tm_hour'],
            parsed_pub_date['tm_min'],
            parsed_pub_date['tm_sec'])
    else:
        pub_date = d.feed.get('published')
        if pub_date != None:
            pub_date = pt_br_date_handler(pub_date)
        else:
            pub_date = datetime.datetime.now()
    # nada para lastBuildDate
    category = d.feed.get('tags', [{}])[0].get('label', None)
    generator = d.feed.get('generator')
    docs = d.feed.get('docs')
    if d.feed.get('cloud') != None:
        cloud = 'domain=' + d.feed.cloud.get('domain') + ' port=' + d.feed.cloud.get('port') + ' path=' + d.feed.cloud.get('path') + ' registerProcedure=' + d.feed.get('registerProcedure') + ' protocol=' + d.feed.get('protocol')
    else:
        cloud = None
    ttl = int(d.feed.get('ttl', 60))
    
    feed = Feed.objects.get_or_create(address=url)[0]
    feed.title = title
    feed.link = link
    feed.description = description
    feed.language = language
    feed.copyright_notice = copyright_notice
    feed.managing_editor = managing_editor
    feed.webmaster = webmaster
    feed.pub_date = pub_date
    feed.category = category
    feed.generator = generator
    feed.docs = docs
    feed.cloud = cloud
    feed.ttl = ttl
    feed.save()
    entries = fetch_entries(d, feed)
    return (feed, entries)


def fetch_entries(d, feed):
    entries = []

    for e in d.entries:
        title = e.get('title', 'No title')
        link = e.get('link', 'http://nolink')
        description = e.get('description', 'no description')
        author = e.get('author_detail', {}).get('email')
        category = e.get('tags', [{}])[0].get('label', None)
        comments = e.get('comments')
        parsed_pub_date = e.get('published_parsed')
        if (parsed_pub_date != None):
            pub_date = datetime.datetime(
                parsed_pub_date.tm_year,
                parsed_pub_date.tm_mon,
                parsed_pub_date.tm_mday,
                parsed_pub_date.tm_hour,
                parsed_pub_date.tm_min,
                parsed_pub_date.tm_sec)
        else:
            pub_date = e.get('published')
            if pub_date != None:
                pub_date = pt_br_date_handler(pub_date)
            else:
                pub_date = datetime.datetime.now()

        entry = Entry.objects.get_or_create(
            title=title,
            link=link,
            description=description,
            author=author,
            category=category,
            comments=comments,
            pub_date=pub_date,
            feed=feed)[0]

        entries.append(entry)
    return entries


# call every 30 min or less
def update_feeds():
    for f in Feed.objects.all():
        collected_entries = fetch_feed(f.address)[1]
        subscribed_users = ReaderUser.objects.filter(feeds__in=[f.address])
        for ru in subscribed_users:
            for e in collected_entries:
                receipt = ReceivedEntry.objects.get_or_create(entry=e, reader_user=ru)[0]


def pt_br_date_handler(date_string):
    pattern = re.compile(
        r'(Seg|Ter|Qua|Qui|Sex|Sáb|Dom),\s(\d{1,2})\s(Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)\s(\d{4})\s(\d{2}):(\d{2}):(\d{2})\s(\+|-)(\d{4})')
    matches = pattern.search(date_string)
    day_of_week, day_of_month, month, year, hour, minute, second, offset_dir, offset_value = matches.groups()
    day_of_week_list = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']
    month_list = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    month = month_list.index(month) + 1
    # FIXME lidar com offset
    return datetime.datetime(int(year), int(month), int(day_of_month), int(hour), int(minute), int(second))
