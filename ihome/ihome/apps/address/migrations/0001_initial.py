# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-07-01 13:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='区域名称')),
            ],
            options={
                'verbose_name': '地区',
                'verbose_name_plural': '地区',
                'db_table': 'ih_area_info',
            },
        ),
    ]
