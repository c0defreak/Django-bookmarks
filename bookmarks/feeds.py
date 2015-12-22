from django.contrib.syndication.views import Feed
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Bookmark


class RecentBookmarks(Feed):
    title = 'Django Bookmarks | Recent'
    link = '/feeds/recent'
    description = 'Recent Bookmarks Posted To Django Bookmarks'

    def items(self):
        return Bookmark.objects.order_by('-id')[:10]

    def item_title(self, item):
        return item.title


class UserBookmarks(Feed):
    def get_object(self, request, user):
        return get_object_or_404(User, username=user)

    def title(self, user):
        return 'Django Bookmarks | Bookmark Posted by %s' % user.username

    def link(self, user):
        return '/feeds/user/%s' % user.username

    def description(self, user):
        return 'Recent bookmark posted by %s' % user.username

    def items(self, user):
        return user.bookmark_set.order_by('-id')[:10]

    def item_title(self, item):
        return item.title
