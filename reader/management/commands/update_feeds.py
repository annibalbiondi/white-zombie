from django.core.management.base import NoArgsCommand, CommandError
from reader import rss

class Command(NoArgsCommand):
    help = 'Fetches for new items on all the feeds present in the database'

    def handle_noargs(self, **options):
        try:
            rss.update_feeds()
        except StandardError:
            raise CommandError('Error: could not update feeds')

        self.stdout.write('All feeds updated')
