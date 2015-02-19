import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','poc_project.settings')
import codecs
import datetime
import random
from reader.models import *
from reader.classification import train_nb, classify

# delimitacoes do periodo de treinamento e classificacao
training_start = datetime.datetime(2014, 2, 9)
training_end = datetime.datetime(2014, 2, 10)
classification_start = datetime.datetime(2014, 2, 10)
classification_end = datetime.datetime(2014, 2, 12)

# extrair noticias a serem classificadas
# serao classificadas todas as noticias posteriores ao periodo de treinamento
training_feeds = {}
training_feeds['sports'] = Feed.objects.filter(address__in=(
    'http://globoesporte.globo.com/servico/semantica/editorias/plantao/feed.rss',
    'http://rss.uol.com.br/feed/noticias.xml',
    'http://g1.globo.com/dynamo/rss2.xml'))
training_feeds['economy'] = Feed.objects.filter(address__in=(
    'http://rss.uol.com.br/feed/noticias.xml',
    'http://g1.globo.com/dynamo/rss2.xml',
    'http://g1.globo.com/dynamo/economia/rss2.xml',
    'http://rss.uol.com.br/feed/economia.xml'))

classification_feeds = Feed.objects.filter(
    address__in=('http://g1.globo.com/dynamo/rss2.xml',
                 'http://rss.uol.com.br/feed/noticias.xml',
                 'http://globoesporte.globo.com/servico/semantica/editorias/plantao/feed.rss',
                 'http://rss.uol.com.br/feed/economia.xml'))

classification_set = []

for feed in classification_feeds:
    classification_set.extend(random.sample(
        Entry.objects.filter(
            feed__in=classification_feeds,
            ).exclude(pub_date__day=9),
        30))

for username in ('sports', 'economy'):
    reader_user = ReaderUser.objects.get(user__username=username)
    feeds = reader_user.feeds
    training_news = Entry.objects.filter(
        feed__in=training_feeds[username],
        pub_date__day=10)
    ignored_news = (Entry.objects.filter(
        feed__in=training_feeds[username]).exclude(
            pub_date__day=10))
    classifier = train_nb(
        reader_user, ignored_news)

    results = []

    for entry in classification_set:
        result = classify(entry, classifier)
        results.append((entry, result))

    # imprimir os resultados em um arquivo
    with codecs.open(
            'resultados.txt',
            'a',
            encoding='utf-8') as results_file:

        results_file.write(username + ':')
        results_file.write('\n')
        results_file.write('\n')
        for entry, result in results:
            results_file.write(entry.title + ' ' + result + '\n' +
                               entry.pub_date.isoformat(' ') + '\n' +
                               entry.link + '\n')
            results_file.write('\n')
        results_file.write('\n')
