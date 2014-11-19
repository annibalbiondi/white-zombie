from django.conf.urls import patterns, url
from reader import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^user', views.user_home, name='user_home'),
    url(r'^click', views.click, name='click'),
    url(r'^dev', views.dev, name='dev'),
    url(r'^feed', views.feed_page, name='feed_page'),
)
