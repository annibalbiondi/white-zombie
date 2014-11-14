# coding=utf-8
import locale
import datetime
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from reader.models import Feed, Entry, ReaderUser, ReadEntry, ReceivedEntry, RecommendedEntry
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from reader.naive_bayes import train_classifier, classify
import feedparser

def user_login(request):
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            request.session['user'] = user.username
            request.session.set_expiry(0)
            return redirect('/reader/feed')
        else:
            # login invalido
            return HttpResponse('invalid login')
    else:
        return render_to_response('/reader', {}, context)


def user_registration(request):
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        
        if User.objects.filter(username=username):
            return HttpResponse('already exists')
        else:
            user = User.objects.create(username=username, email=email, password=password)
            user.set_password(user.password)
            user.save()
            u = ReaderUser.objects.create(user=user)
            u.save()
            request.session['user'] = user.username
        
        return HttpResponse('user ' + username + ' created')
    else:
        return HttpResponse('no post, no service')


def dev(request):
    context = RequestContext(request)

    u = User.objects.get(username='test_user')
    user = u.reader_user
    feeds = user.feeds.all()
    entries_received = user.entries_received.all()
    entries_read = [e.entry for e in user.entries_read.all()]

    # has the user seen anything?
    if user.entries_received.filter(showed_to_user=True).exists():
        if user.entries_received.filter(showed_to_user=False).exists():
            classifier = train_classifier(user)
            unseen_receipts = user.entries_received.filter(showed_to_user=False)
            new_entries = [r.entry for r in unseen_receipts]
            print 'new_entries:'
            print new_entries
            for e in new_entries:
                category = classify(e, classifier)
                print e, category
                if category == 'read':
                    re = RecommendedEntry.objects.get_or_create(entry=e)[0]
                    user.entries_recommended.add(re)

            # ja que, por agora, todas sao mostradas, todas serao marcadas como tal
            for e in new_entries:
                receipt = ReceivedEntry.objects.get(entry=e)
                receipt.showed_to_user = True
                receipt.save()

            user.save()

    entries_received = [r.entry for r in user.entries_received.all().order_by('-entry__pub_date')]
    entries_recommended = [r.entry for r in user.entries_recommended.all()]

    context_dict = {
        'user': user,
        'feeds': feeds,
        'entries_received': entries_received,
        'entries_read': entries_read,
        'entries_recommended': entries_recommended
        }

    # caguei aqui
    return render_to_response('reader/test_page.html', context_dict, context)


def click(request):
    context = RequestContext(request)

    u = User.objects.get(email=request.GET['user'])
    user = u.reader_user
    link = request.GET['url']
    clicked_entry = Entry.objects.get(link=link)
    entryRead = ReadEntry.objects.get_or_create(
        entry=clicked_entry)[0]
    user.entries_read.add(entryRead)
    entryReceived = ReceivedEntry.objects.get(entry=clicked_entry)
    entryReceived.showed_to_user = True
    entryReceived.save()
#    if user.entries_recommended.filter(entry=clicked_entry).exists():
 #       er = user.entries_recommended.get(entry=clicked_entry)
  #      user.entries_recommended.remove(er)
   #     er.delete()
    user.save()
    return redirect(link)


def user_home(request):
    context = RequestContext(request)
    # TODO conseguir o user
    context_dict = {
        'user': user,
        'feeds': Feed.objects.all(),
        'entries': Entry.objects.order_by('-pub_date')
        }

    return render_to_response('reader/user_home.html', context_dict, context)


def index(request):
    context = RequestContext(request)

    context_dict = {}

    return render_to_response('reader/index.html', context_dict, context)


@login_required
def feed_page(request):
    context = RequestContext(request)
    
    # como pegar o usuario? do cookie!
    u = User.objects.get(username=request.session['user'])
    user = u.reader_user
    feed_list = user.feeds.all()
    # como pegar o feed desejado? seu nome esta no URL
    
    feed = Feed.objects.get(title='UOL Notícias')
    entries = user.entries_received.filter(entry__feed=feed).order_by('-entry__pub_date')
    entries = [r.entry for r in entries]

    if request.method == 'POST':
        link = request.POST['feed_link']
        
        d = feedparser.parse(link)
        feed = Feed.objects.get_or_create(
            title=d.feed.title,
            link=d.feed.link,
            description=d.feed.description)[0]
        feed.save()
        reader_user = u.reader_user
        reader_user.feeds.add(feed)
        reader_user.save()
        print 'user ' + u.username + ' assinou feed ' + feed.title
    
    context_dict = {
        'user': user,
        'feed': feed,
        'feed_list': feed_list,
        'entries': entries,
        }

    return render_to_response('reader/feed_page.html', context_dict, context)
