import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','poc_project.settings')
import codecs
import datetime
from reader.models import *
from reader.classification import train_nb, classify

# delimitacoes do periodo de treinamento
start_date = datetime.datetime(2014, 2, 9)
end_date = datetime.datetime(2014, 2, 10)

# extrair notícias a serem classificadas
# serao classificadas todas as noticias posteriores ao periodo de treinamento
feed_list = Feed.objects.filter(address__in((
    'http://g1.globo.com/dynamo/rss2.xml',
    'http://g1.globo.com/dynamo/economia/rss2.xml',
    'http://rss.uol.com.br/feed/noticias.xml',
    'http://rss.uol.com.br/feed/economia.xml',
    'http://globoesporte.globo.com/servico/semantica/editorias/plantao/feed.rss',
    'http://esporte.uol.com.br/ultimas/index.xml')))
     
# TODO definir se serao classificadas noticias de todos os feeds
# ou apenas aquelas dos feeds gerais
classification_set = Entry.objects.filter(feed__in=feed_list,
                                          pub_date__gt=end_date))

for username in ('sports', 'economy'):
    reader_user = ReaderUser.objects.get(user__username=username)
    feeds = reader_user.feeds
    discarded_news = ReceivedEntry.objects.exclude(
        entry__pub_date__range(start_date, end_date))

    classifier = train_nb(
        reader_user,
        list(discarded_news).extend(
            ReceivedEntry.objects.filter(entry__in=classification_set))

    results = []

    for entry in classification_set:
        result = classify(entry, classifier)
        results.add((entry, result))

    # imprimir os resultados em um arquivo
    with codecs.open(
            'resultados.txt',
            'w',
            encoding='utf-8') as results_file:

        results_file.write(username + ':')
        results_file.write()
        results_file.write()
        for entry, result in results:
            results_file.write(entry.title + ' ' + result)
            results_file.write()
        results_file.write()
