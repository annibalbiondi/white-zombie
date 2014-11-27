# coding=utf-8
import locale
import datetime
import feedparser
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from reader.classification import train_nb, train_positivenb, classify
from reader.forms import RegisterForm, LoginForm, FeedSubscriptionForm
from reader.models import Feed, Entry, ReaderUser, ReadEntry, ReceivedEntry, RecommendedEntry
from reader import rss

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

@login_required
def click(request):
    context = RequestContext(request)

    user = User.objects.get(username=request.session['user'])
    reader_user = user.reader_user
    link = request.GET['url']
    clicked_entry = Entry.objects.get(link=link)
    readEntry = ReadEntry.objects.get_or_create(
        entry=clicked_entry, reader_user=reader_user)[0]
    receivedEntry = ReceivedEntry.objects.get(
        entry=clicked_entry,
        reader_user=reader_user)
    receivedEntry.showed_to_user = True # caso ainda não tenha sido
    receivedEntry.save()
    # if user.entries_recommended.filter(entry=clicked_entry).exists():
    #     er = user.entries_recommended.get(entry=clicked_entry)
    #     user.entries_recommended.remove(er)
    #     er.delete()
    return redirect(link)


@login_required
def user_home(request):
    context = RequestContext(request)
    user = User.objects.get(username=request.session['user'])

    context_dict = {}

    return render_to_response('reader/user_home.html', context_dict, context)


def index(request):
    context = RequestContext(request)

    if request.method == 'POST':
        if 'register-submit' in request.POST:
            register_form = RegisterForm(request.POST,
                                         auto_id='register-%s')
            if register_form.is_valid():
                user = register_form.save()
                user.set_password(user.password)
                user.save()
                reader_user = ReaderUser.objects.create(user=user)
                reader_user.save()
                # login with user
                user = authenticate(
                    username=request.POST['username'],
                    password=request.POST['password'])
                if user:
                    login(request, user)
                    request.session['user'] = user.username
                    request.session.set_expiry(0)
                    return redirect('/reader/feed')
            login_form = LoginForm(auto_id='login-%s')
        elif 'login-submit' in request.POST:
            login_form = LoginForm(request.POST,
                                   auto_id='login-%s')
            if login_form.is_valid():
                user = authenticate(
                    username=request.POST['username'],
                    password=request.POST['password'])
                if user:
                    login(request, user)
                    request.session['user'] = user.username
                    request.session.set_expiry(0)
                    return redirect('/reader/feed')
            register_form = RegisterForm(auto_id='register-%s')
        elif 'logout' in request.POST:
            logout(request)
            register_form = RegisterForm(auto_id='register-%s')
            login_form = LoginForm(auto_id='login-%s')
    elif 'user' in request.session:
        return redirect('/reader/feed')
    else:
        register_form = RegisterForm(auto_id='register-%s')
        login_form = LoginForm(auto_id='login-%s')
    
    context_dict = {
        'register_form': register_form,
        'login_form': login_form,
    }

    return render_to_response('reader/index.html', context_dict, context)


@login_required
def feed_page(request):
    context = RequestContext(request)
    
    user = User.objects.get(username=request.session['user'])
    reader_user = user.reader_user
    feed_list = reader_user.feeds.all()
    feed = None

    if request.method == 'POST':
        if 'subscription-submit' in request.POST:
            feed_sub_form = FeedSubscriptionForm(request.POST,
                                                 auto_id='feed-%s')
            if feed_sub_form.is_valid():
                feed = rss.fetch_feed(feed_sub_form.cleaned_data['link'])[0]
                reader_user.feeds.add(feed)
                for e in Entry.objects.filter(feed=feed).order_by('-pub_date')[:100]:
                    received_entry = ReceivedEntry.objects.get_or_create(entry=e, reader_user=reader_user)[0]
                    received_entry.save()
                reader_user.save()
                # redirecionar para a página do feed recém-assinado
                
        elif 'subscription-cancelation' in request.POST:
            feed_address = request.POST['address']
            feed_to_unsubscribe = Feed.objects.get(address=feed_address)
            reader_user.feeds.remove(feed_to_unsubscribe)
            reader_user.save()
        feed_sub_form = FeedSubscriptionForm(auto_id='feed-%s')
    elif request.method == 'GET':
        feed_address = request.GET.get('address')
        if (feed_address != None):
            feed = Feed.objects.get(address=feed_address)
        feed_sub_form = FeedSubscriptionForm(auto_id='feed-%s')
    else:
        feed_sub_form = FeedSubscriptionForm(auto_id='feed-%s')

    if feed != None:
        received_entries = ReceivedEntry.objects.filter(entry__feed=feed).filter(reader_user=reader_user).order_by('-entry__pub_date')
        entries = [r.entry for r in received_entries]
    
        if ReadEntry.objects.filter(reader_user=reader_user, entry__feed=feed).exists():
            classifier = train_positivenb(reader_user, feed=feed)
            classifier.show_most_informative_features()
            # classify stuff
            for receipt in received_entries:
                label = classify(receipt.entry, classifier)
                if receipt.showed_to_user == False:
                    receipt.showed_to_user = True
                    receipt.save()
                    if label == True:
                        recommended = RecommendedEntry.objects.get_or_create(entry=receipt.entry, reader_user=reader_user)[0]
                        print recommended.entry
                        # implementar gatilhos de classificação
    else:
        entries = None

    context_dict = {
        'user': reader_user,
        'feed': feed,
        'feed_list': feed_list,
        'entries': entries,
        'feed_sub_form': feed_sub_form,
        }

    return render_to_response('reader/feed_page.html', context_dict, context)
