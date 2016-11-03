# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-03 17:36
from __future__ import unicode_literals

import Flights140base.models
from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('plural_names', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('additional_keywords', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('abbreviations', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('iata', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('place_id', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=5000)),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('plural_names', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('additional_keywords', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('abbreviations', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('place_id', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('plural_names', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('additional_keywords', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('abbreviations', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('place_id', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('plural_names', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('additional_keywords', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('abbreviations', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('place_id', models.CharField(blank=True, max_length=100, null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Country')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Region')),
            ],
        ),
        migrations.CreateModel(
            name='Subregion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('plural_names', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('additional_keywords', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('abbreviations', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('place_id', models.CharField(blank=True, max_length=100, null=True)),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Region')),
            ],
        ),
        migrations.CreateModel(
            name='Tweet',
            fields=[
                ('tweet_id', models.BigIntegerField(primary_key=True, serialize=False, unique=True)),
                ('tweet', models.CharField(max_length=160)),
                ('from_keywords', django.contrib.postgres.fields.jsonb.JSONField()),
                ('to_keywords', django.contrib.postgres.fields.jsonb.JSONField()),
                ('timestamp', models.DateTimeField()),
                ('parsed', models.BooleanField(default=True)),
            ],
            options={
                'get_latest_by': 'tweet_id',
            },
        ),
        migrations.CreateModel(
            name='TwitterAccount',
            fields=[
                ('user_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('full_name', models.CharField(max_length=50)),
                ('screen_name', models.CharField(max_length=50)),
            ],
            options={
                'get_latest_by': 'full_name',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, max_length=16, null=True, validators=[Flights140base.models.twilio_validate])),
                ('email', models.EmailField(blank=True, max_length=254, null=True, validators=[Flights140base.models.mailgun_validate])),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='tweet',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.TwitterAccount'),
        ),
        migrations.AddField(
            model_name='state',
            name='subregion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Subregion'),
        ),
        migrations.AddField(
            model_name='country',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Region'),
        ),
        migrations.AddField(
            model_name='country',
            name='subregion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Subregion'),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Flights140base.UserProfile'),
        ),
        migrations.AddField(
            model_name='city',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Country'),
        ),
        migrations.AddField(
            model_name='city',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Region'),
        ),
        migrations.AddField(
            model_name='city',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.State'),
        ),
        migrations.AddField(
            model_name='city',
            name='subregion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='Flights140base.Subregion'),
        ),
        migrations.AddField(
            model_name='alert',
            name='from_city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='from_city', to='Flights140base.City'),
        ),
        migrations.AddField(
            model_name='alert',
            name='from_country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='from_country', to='Flights140base.Country'),
        ),
        migrations.AddField(
            model_name='alert',
            name='from_region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='from_region', to='Flights140base.Region'),
        ),
        migrations.AddField(
            model_name='alert',
            name='from_state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='from_state', to='Flights140base.State'),
        ),
        migrations.AddField(
            model_name='alert',
            name='from_subregion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='from_subregion', to='Flights140base.Subregion'),
        ),
        migrations.AddField(
            model_name='alert',
            name='to_city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='to_city', to='Flights140base.City'),
        ),
        migrations.AddField(
            model_name='alert',
            name='to_country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='to_country', to='Flights140base.Country'),
        ),
        migrations.AddField(
            model_name='alert',
            name='to_region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='to_region', to='Flights140base.Region'),
        ),
        migrations.AddField(
            model_name='alert',
            name='to_state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='to_state', to='Flights140base.State'),
        ),
        migrations.AddField(
            model_name='alert',
            name='to_subregion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='to_subregion', to='Flights140base.Subregion'),
        ),
        migrations.AddField(
            model_name='alert',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Flights140base.UserProfile'),
        ),
    ]