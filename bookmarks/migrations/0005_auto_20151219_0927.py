# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookmarks', '0004_sharedbookmark'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sharedbookmark',
            name='bookmark',
            field=models.OneToOneField(to='bookmarks.Bookmark'),
        ),
    ]
