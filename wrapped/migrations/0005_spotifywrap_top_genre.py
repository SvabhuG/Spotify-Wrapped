# Generated by Django 4.2 on 2024-12-01 02:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wrapped', '0004_spotifyprofile_expires_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='spotifywrap',
            name='top_genre',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]