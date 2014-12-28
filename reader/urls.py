from django.conf.urls import patterns, url
from reader import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^click', views.click, name='click'),
    url(r'^dev', views.dev, name='dev'),
    url(r'^feed', views.feed_page, name='feed_page'),
)
