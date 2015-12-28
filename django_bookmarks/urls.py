"""django_bookmarks URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from bookmarks.views import *
from bookmarks.feeds import *

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^comments/', include('django_comments.urls')),
    # Feeds
    url(r'^feeds/$', RecentBookmarks()),
    url(r'^feeds/user/(\w+)/$', UserBookmarks()),
    # Browsing
    url(r'^$', main_page),
    url(r'^user/(\w+)/$', user_page),
    url(r'^tag/([^\s]+)/$', tag_page),
    url(r'^tag/$', tag_cloud_page),
    url(r'^search/$', search_page),
    url(r'^popular/$', popular_page),
    url(r'^bookmark/(\d+)/$', bookmark_page),
    url(r'^posted/(\d+)/$', posted_page),

    # session management
    url(r'^login/$', login_page),  # 'django.contrib.auth.views.login'
    url(r'^logout/$', logout_page),
    url(r'^register/$', register_page),
    url(r'^register/success/$', TemplateView.as_view(template_name='registration/register_success.html')),

    # Account management
    url(r'^save/$', bookmark_save_page),
    url(r'^vote/$', bookmark_vote_page),

    # Ajax
    url(r'^ajax/tag/autocomplete/$', ajax_tag_autocomplete),

    # Friends
    url(r'^friends/(\w+)/$', friends_page),
    url(r'^friend/add/$', friend_add)
]
