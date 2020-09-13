# Generated by Django 3.1.1 on 2020-09-13 09:33

from django.db import migrations, models
import django_countries.fields
import timezone_field.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Community',
            fields=[
                ('handle', models.SlugField(help_text='Once you set this, it cannot be changed. Pick carefully as this will be the identifier to find your community leaderboard.', primary_key=True, serialize=False, verbose_name='Handle')),
                ('language', models.CharField(choices=[('en', 'English'), ('de', 'German'), ('es', 'Spanish'), ('fr', 'French'), ('it', 'Italian'), ('ja', 'Japanese'), ('ko', 'Korean'), ('pt-br', 'Brazilian Portuguese'), ('th', 'Thai'), ('zh-hant', 'Traditional Chinese')], default='en-us', max_length=7, verbose_name='language')),
                ('timezone', timezone_field.fields.TimeZoneField(default='UTC', verbose_name='timezone')),
                ('country', django_countries.fields.CountryField(blank=True, help_text='Where your community is based', max_length=2, null=True, verbose_name='country')),
                ('name', models.CharField(help_text='Max 70 characters', max_length=70, verbose_name='name')),
                ('description', models.TextField(blank=True, help_text='What makes your community unique? What are you about?', null=True, verbose_name='description')),
                ('can_see', models.BooleanField(default=False, help_text='Default: False\nTurn this on to share your community with the world.', verbose_name='Publicly Viewable')),
                ('can_join', models.BooleanField(default=False, help_text='Default: False\nTurn this on to make your community free to join. No invites required.', verbose_name='Publicly Joinable')),
            ],
            options={
                'verbose_name': 'community',
                'verbose_name_plural': 'communities',
            },
        ),
    ]