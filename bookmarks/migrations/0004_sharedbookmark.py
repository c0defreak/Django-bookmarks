# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bookmarks', '0003_tag'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedBookmark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('votes', models.IntegerField(default=1)),
                ('bookmark', models.ForeignKey(to='bookmarks.Bookmark', unique=True)),
                ('users_voted', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
