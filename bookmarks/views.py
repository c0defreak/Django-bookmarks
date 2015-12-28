import json
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import *
from .models import *


ITEMS_PER_PAGE = 3
# Create your views here.


def main_page(request):
    shared_bookmarks = SharedBookmark.objects.order_by(
        '-date'
        )[:10]
    variables = {
        'user': request.user,
        'shared_bookmarks': shared_bookmarks
    }

    return render(request, 'bookmarks/main_page.html', context=variables)


def user_page(request, username):
    user = get_object_or_404(User, username=username)
    query_set = user.bookmark_set.order_by('-id')
    paginator = Paginator(query_set, ITEMS_PER_PAGE)
    is_friend = Friendship.objects.filter(
        from_friend=request.user,
        to_friend=user
    )
    page = request.GET.get('page')
    try:
        bookmarks = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integet, deliver first page
        bookmarks = paginator.page(1)
    except EmptyPage:
        bookmarks = paginator.page(paginator.num_pages)
    variables = {
        'username': username,
        'bookmarks': bookmarks,
        'show_tags': True,
        'show_edit': username == request.user.username,
        'is_friend': is_friend
    }
    return render(request, 'bookmarks/user_page.html', context=variables)


def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')


def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email'],
            )
            user.save()
            return HttpResponseRedirect('/register/success/')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required(login_url='/login/')
def bookmark_save_page(request):
    ajax = 'ajax' in request.GET
    if request.method == 'POST':
        form = BookmarkSaveForm(request.POST)
        if form.is_valid():
            bookmark = _bookmark_save(request, form)
            if ajax:
                variables = {
                    'bookmarks': [bookmark],
                    'show_edit': True,
                    'show_tags': True
                }
                return render(request,
                              'bookmarks/bookmark_list.html',
                              context=variables)
            else:
                return HttpResponseRedirect(
                    '/user/%s/' % request.user.username
                )
        else:
            if ajax:
                return HttpResponse('failure')
    elif 'url' in request.GET:
        url = request.GET['url']
        title = ''
        tags = ''
        try:
            link = Link.objects.get(url=url)
            bookmark = Bookmark.objects.get(
                link=link,
                user=request.user
            )
            title = bookmark.title
            tags = " ".join(
                tag.name for tag in bookmark.tag_set.all()
            )
        except ObjectDoesNotExist:
            pass
        form = BookmarkSaveForm({
            'url': url,
            'title': title,
            'tags': tags
        })
    else:
        form = BookmarkSaveForm()
    if ajax:
        return render(request,
                      'bookmarks/bookmark_save_form.html',
                      {'form': form})
    else:
        return render(request, 'bookmarks/bookmark_save.html', {'form': form})


def tag_page(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    bookmarks = tag.bookmarks.order_by('-id')
    variables = {
        'bookmarks': bookmarks,
        'tag_name': tag_name,
        'show_tags': True,
        'show_user': True
    }
    return render(request, 'bookmarks/tag_page.html', context=variables)


def tag_cloud_page(request):
    MAX_WEIGHT = 5
    tags = Tag.objects.order_by('name')
    # calculate tag, min and max counts
    min_count = max_count = tags[0].bookmarks.count()
    for tag in tags:
        tag.count = tag.bookmarks.count()
        if tag.count < min_count:
            min_count = tag.count
        if max_count < tag.count:
            max_count = tag.count
    # calculate count range. Avoid dividing by zero.
    range = float(max_count - min_count)
    if range == 0.0:
        range = 1.0
    # calculate tag weights.
    for tag in tags:
        tag.weight = int(
            MAX_WEIGHT * (tag.count - min_count) / range
        )
    variables = {
        'tags': tags
    }
    return render(request, 'bookmarks/tag_cloud_page.html', context=variables)


def search_page(request):
    form = SearchForm()
    bookmarks = []
    show_results = False
    if 'query' in request.GET:
        show_results = True
        query = request.GET['query'].strip()
        if query:
            keywords = query.split()
            q = Q()
            for keyword in keywords:
                q = q & Q(title__icontains=keyword)
            form = SearchForm({'query': query})
            bookmarks = Bookmark.objects.filter(q)[:10]
    variables = {
        'form': form,
        'bookmarks': bookmarks,
        'show_results': show_results,
        'show_tags': True,
        'show_user': True
    }
    if 'ajax' in request.GET:
        return render(request, 'bookmarks/bookmark_list.html',
                      context=variables)
    else:
        return render(request, 'bookmarks/search.html', context=variables)


def _bookmark_save(request, form):
    # Create or get link
    link, dummy = Link.objects.get_or_create(
        url=form.cleaned_data['url']
    )
    # Create or get bookmark
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        link=link
    )
    # Update bookmark title
    bookmark.title = form.cleaned_data['title']
    if not created:
        bookmark.tag_set.clear()
    # Create a new tag list
    tag_names = form.cleaned_data['tags'].split()
    for tag_name in tag_names:
        tag, dummy = Tag.objects.get_or_create(name=tag_name)
        bookmark.tag_set.add(tag)
    # Share on the main page if requested
    if form.cleaned_data['share']:
        shared_bookmark, created = SharedBookmark.objects.get_or_create(
            bookmark=bookmark
            )
        if created:
            shared_bookmark.users_voted.add(request.user)
            shared_bookmark.save()
    # Save bookmark to database and return it
    bookmark.save()
    return bookmark


# Reimplemented as the mentioned plugin is depreceated
def ajax_tag_autocomplete(request):
    if request.is_ajax():
        term = request.GET.get('term', '')
        tags = \
            Tag.objects.filter(name__istartswith=term)[:10]
        results = []
        for tag in tags:
            tag_json = {}
            tag_json['value'] = tag.name
            results.append(tag_json)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


@login_required(login_url='/login/')
def bookmark_vote_page(request):
    if 'id' in request.GET:
        try:
            id = request.GET['id']
            shared_bookmark = SharedBookmark.objects.get(id=id)
            user_voted = shared_bookmark.users_voted.filter(
                username=request.user.username
                )
            if not user_voted:
                shared_bookmark.votes += 1
                shared_bookmark.users_voted.add(request.user)
                shared_bookmark.save()
        except ObjectDoesNotExist:
            raise Http404('Bookmark not found.')
    if 'HTTP_REFERER' in request.META:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    return HttpResponseRedirect('/')


def popular_page(request):
    today = datetime.today()
    day = today - timedelta(10)
    shared_bookmarks = SharedBookmark.objects.filter(
        date__gt=day
        )
    shared_bookmarks = shared_bookmarks.order_by(
        '-votes'
        )[:10]
    variables = {
        'shared_bookmarks': shared_bookmarks
    }
    return render(request, 'bookmarks/popular_page.html', context=variables)


def bookmark_page(request, bookmark_id):
    shared_bookmark = get_object_or_404(
        SharedBookmark,
        id=bookmark_id
        )
    variables = {
        'shared_bookmark': shared_bookmark
    }
    return render(request, 'bookmarks/bookmark_page.html', context=variables)


def friends_page(request, username):
    user = get_object_or_404(User, username=username)
    friends = \
        [friendship.to_friend for friendship in user.friend_set.all()]
    friend_bookmarks = \
        Bookmark.objects.filter(user__in=friends).order_by('-id')
    paginator = Paginator(friend_bookmarks, ITEMS_PER_PAGE)
    page = request.GET.get('page')
    try:
        bookmarks = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integet, deliver first page
        bookmarks = paginator.page(1)
    except EmptyPage:
        bookmarks = paginator.page(paginator.num_pages)
    variables = {
        'username': username,
        'friends': friends,
        'bookmarks': bookmarks,
        'show_tags': True,
        'show_user': True
    }
    return render(request, 'bookmarks/friends_page.html', context=variables)


@login_required(login_url='/login/')
def friend_add(request):
    if 'username' in request.GET:
        friend = \
            get_object_or_404(User, username=request.GET['username'])
        friendship = Friendship(
            from_friend=request.user,
            to_friend=friend
        )
        friendship.save()
        return HttpResponseRedirect(
            '/friends/%s/' % request.user.username
        )
    else:
        raise Http404


def posted_page(request, id):
    try:
        shared_bookmark = SharedBookmark.objects.get(id=id)
    except ObjectDoesNotExist:
        raise Http404('Object does not exist')
    variables = {
        'shared_bookmark': shared_bookmark
    }
    return render(request, 'bookmarks/posted.html', context=variables)


def login_page(request):
    state = "Please Log in Below"
    next = ""
    if request.GET:
        next = request.GET['next']
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                state = "log in successful"
                if next == "":
                    return HttpResponseRedirect('/')
                else:
                    return HttpResponseRedirect(next)
            else:
                state = "Your Account is not active"
        else:
            state = "username or password incorrect"
    variables = {
        'state': state,
        'next': next
    }
    return render(request, 'bookmarks/login.html', context=variables)
