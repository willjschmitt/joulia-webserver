# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-19 17:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0024_auto_20171112_1455'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrewingState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField()),
                ('name', models.TextField()),
                ('description', models.TextField(default='')),
                ('software_release', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='brewery.JouliaControllerRelease')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='brewingstate',
            unique_together=set([('software_release', 'index')]),
        ),
    ]
