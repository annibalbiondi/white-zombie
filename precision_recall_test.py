os.environ.setdefault('DJANGO_SETTINGS_MODULE','poc_project.settings')
from reader.models import *
from reader.classification import train_nb, classify

# treinar classificador para o usuario de esportes
# extrair notícias a serem classificadas

classification_set = Entry.objects.filter(feed__in=feed_list) # noticias de um determinado periodo

results = {}

for username in ('sports', 'economy'):
    reader_user = ReaderUser.objects.get(user__username=username)
    feeds = reader_user.feeds
    discarded_news = ReceivedEntry.objects.filter(entry__feed__in=feeds) # após uma certa data

    classifier = train_nb(
        reader_user,
        list(discarded_news).extend(
            ReceivedEntry.objects.filter(entry__in=classification_set))

    results[username] = []

    for entry in classification_set:
        result = classify(entry, classifier)
        results[username].add((entry, result))

# imprimir os resultados em um arquivo
