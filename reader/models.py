from django.db import models
from django.contrib.auth.models import User

class Feed(models.Model):
    address = models.URLField(primary_key=True)
    title = models.CharField(max_length=128)
    link = models.URLField()
    description = models.TextField()
    language = models.CharField(max_length=16, null=True)
    copyright_notice = models.CharField(max_length=64, null=True)
    managing_editor = models.EmailField(null=True)
    webmaster = models.EmailField(null=True)
    pub_date = models.DateTimeField(null=True)
    last_build_date = models.DateTimeField(null=True)
    category = models.CharField(max_length=64, null=True)
    generator = models.CharField(max_length=64, null=True)
    docs = models.URLField(null=True)
    cloud = models.CharField(max_length=256, null=True)
    ttl = models.IntegerField(null=True)
#    image = ImageField(null=True) # TODO criar MEDIA_ROOT e MEDIA_URL em settings.py
    # rating = # TODO descobrir o que eh PICS e POWDER
    skip_hours = models.CommaSeparatedIntegerField(max_length=128)
    # skip_days # TODO criar campo customizado para isso
        
    def __unicode__(self):
        return self.title


class Entry(models.Model):
    title = models.CharField(max_length=128, null=True)
    link = models.URLField(null=True)
    description = models.TextField()
    author = models.EmailField(null=True)
    category = models.CharField(max_length=64, null=True)
    comments = models.URLField(null=True)
    enclosure = models.CharField(max_length=512, null=True)
    # guid
    pub_date = models.DateTimeField();
    # source = 
    feed = models.ForeignKey(Feed)

    def __unicode__(self):
        return self.title


class ReaderUser(models.Model):
    user = models.OneToOneField(User, primary_key=True, related_name='reader_user')
    feeds = models.ManyToManyField(Feed)

    def __unicode__(self):
        return self.user.username


class ReceivedEntry(models.Model):
    entry = models.ForeignKey(Entry)
    showed_to_user = models.BooleanField(default=False)
    reader_user = models.ForeignKey(ReaderUser)

    def __unicode__(self):
        return self.entry.__unicode__() + ' ' + self.reader_user.__unicode__()


class RecommendedEntry(models.Model):
    entry = models.ForeignKey(Entry)
    date = models.DateTimeField(auto_now_add=True)
    user_sessions_since = models.IntegerField(default=0)
    reader_user = models.ForeignKey(ReaderUser)

    def __unicode__(self):
        return self.entry.__unicode__() + ' ' + self.reader_user.__unicode__()


class ReadEntry(models.Model):
    entry = models.ForeignKey(Entry)
    date = models.DateTimeField(auto_now_add=True)
    reader_user = models.ForeignKey(ReaderUser)

    def __unicode__(self):
        return self.entry.__unicode__() + ' ' + self.reader_user.__unicode__()
