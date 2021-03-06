# coding=utf-8
import locale
import datetime
import feedparser
import random
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.http import urlquote
from reader.classification import train_nb, classify
from reader.forms import RegisterForm, LoginForm, FeedSubscriptionForm
from reader.models import Feed, Entry, ReaderUser, ReadEntry, ShownEntry, RecommendedEntry
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
                shown_entry = ShownEntry.objects.get_or_create(entry=e, reader_user=user)[0]
                shown_entry.save()

            user.save()

    entries_received = [r.entry for r in user.entries_received.all()
                        .order_by('-entry__pub_date')]
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
    entry_id = request.GET['id']
    clicked_entry = Entry.objects.get(id=entry_id)
    link = clicked_entry.link
    read_entry = ReadEntry.objects.get_or_create(
        entry=clicked_entry, reader_user=reader_user)[0]
    read_entry.save()
    shown_entry = ShownEntry.objects.get_or_create(
        entry=clicked_entry, reader_user=reader_user)[0]
    shown_entry.save()
    if RecommendedEntry.objects.filter(
            reader_user=reader_user,
            entry=clicked_entry).exists():
        er = RecommendedEntry.objects.get(
            reader_user=reader_user,
            entry=clicked_entry)
        er.delete()
    return redirect(link)


def index(request):
    context = RequestContext(request)

    if 'user' in request.session:
        user = User.objects.get(username=request.session['user'])
        reader_user = user.reader_user
        feed_list = reader_user.feeds.all()
        feed_sub_form = FeedSubscriptionForm(auto_id='feed-%s')
        
        if request.method == 'POST':
            if 'logout' in request.POST:
                logout(request)
                register_form = RegisterForm(auto_id='register-%s')
                login_form = LoginForm(auto_id='login-%s')

                context_dict = {
                    'register_form': register_form,
                    'login_form': login_form,
                }

                return render_to_response('reader/index.html', context_dict, context)
            elif 'subscription-submit' in request.POST:
                feed_sub_form = FeedSubscriptionForm(request.POST,
                                                     auto_id='feed-%s')
                if feed_sub_form.is_valid():
                    feed = rss.fetch_feed(feed_sub_form.cleaned_data['link'])[0]
                    reader_user.feeds.add(feed)
                    reader_user.save()
                    # redirecionar para a página do feed recém-assinado
                    redirect('/reader/feed?address=' + urlquote(feed.address))
            elif 'subscription-cancelation' in request.POST:
                feed_address = request.POST['address']
                feed_to_unsubscribe = Feed.objects.get(address=feed_address)
                reader_user.feeds.remove(feed_to_unsubscribe)
                reader_user.save()

        recommended_entries = []
        recent_entries = []
        if RecommendedEntry.objects.filter(reader_user=reader_user).count() >= 3:
            recommended_entries = random.sample(
                RecommendedEntry.objects.filter(reader_user=reader_user), 3)
        if Entry.objects.filter(feed__in=feed_list).count() >= 3:
            recent_entries = Entry.objects.filter(
                feed__in=feed_list).order_by('-pub_date')[:3]
            for entry in recent_entries:
                shown_entry = ShownEntry.objects.get_or_create(
                    reader_user=reader_user,
                    entry=entry)[0]
                shown_entry.save()

        context_dict = {
            'user': reader_user,
            'feed_list': feed_list,
            'feed_sub_form': feed_sub_form,
            'recommended_entries': recommended_entries,
            'recent_entries': recent_entries,
        }

        return render_to_response('reader/user_home.html', context_dict, context)
    else:
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
                    # log user in
                    user = authenticate(
                        username=request.POST['username'],
                        password=request.POST['password'])
                    if user:
                        login(request, user)
                        request.session['user'] = user.username
                        request.session.set_expiry(0)
                        return redirect('/reader')
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
                        return redirect('/reader')
                register_form = RegisterForm(auto_id='register-%s')
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
    recommended_entries = []
    to_be_shown = None
    page = None

    if request.method == 'POST':
        if 'subscription-submit' in request.POST:
            feed_sub_form = FeedSubscriptionForm(request.POST,
                                                 auto_id='feed-%s')
            if feed_sub_form.is_valid():
                feed = rss.fetch_feed(feed_sub_form.cleaned_data['link'])[0]
                reader_user.feeds.add(feed)
                reader_user.save()
                # redirecionar para a página do feed recém-assinado
                redirect('/reader/feed?address=' + urlquote(feed.address))
        elif 'subscription-cancelation' in request.POST:
            feed_address = request.POST['address']
            feed_to_unsubscribe = Feed.objects.get(address=feed_address)
            reader_user.feeds.remove(feed_to_unsubscribe)
            reader_user.save()
        elif 'update-feeds' in request.POST:
            rss.update_feeds()
        feed_sub_form = FeedSubscriptionForm(auto_id='feed-%s')
    elif request.method == 'GET':
        feed_address = request.GET.get('address')
        page = request.GET.get('page')
        if feed_address != None:
            feed = Feed.objects.get(address=feed_address)
        feed_sub_form = FeedSubscriptionForm(auto_id='feed-%s')
    else:
        feed_sub_form = FeedSubscriptionForm(auto_id='feed-%s')

    if feed != None:
        received_entries = Entry.objects.filter(
            feed=feed).order_by('-pub_date')
        paginator = Paginator(received_entries, 15)

        try:
            to_be_shown = paginator.page(page)
        except PageNotAnInteger:
            to_be_shown = paginator.page(1)
        except EmptyPage:
            to_be_shown = paginator.page(paginator.num_pages)
    
        if ShownEntry.objects.filter(
                reader_user=reader_user).exists():
            read_entries = ReadEntry.objects.filter(
                reader_user=reader_user,
                entry__feed=feed)
            classifier = train_nb(reader_user, to_be_shown, feed=feed)
            # classify stuff
            for receipt in [
                    r
                    for r in to_be_shown
                    if r not in [e.entry for e in read_entries]]:
                label = classify(receipt, classifier)
                #print receipt, label
                receipt.save()
                if label == 'interesting':
                    recommended = RecommendedEntry.objects.get_or_create(
                        entry=receipt,
                        reader_user=reader_user)[0]
                    recommended.save()
                    recommended_entries.append(recommended.entry)
                elif RecommendedEntry.objects.filter(
                        reader_user=reader_user,
                        entry=receipt).exists():
                    RecommendedEntry.objects.filter(
                        reader_user=reader_user,
                        entry=receipt).delete()

        for entry in to_be_shown:
            ShownEntry.objects.get_or_create(reader_user=reader_user,
                                             entry=entry)[0].save()

    context_dict = {
        'user': reader_user,
        'feed': feed,
        'feed_list': feed_list,
        'entries': to_be_shown,
        'feed_sub_form': feed_sub_form,
        'recommended_entries': recommended_entries,
    }

    return render_to_response('reader/feed_page.html', context_dict, context)
