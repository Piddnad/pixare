# Generated by Django 2.1.2 on 2018-12-27 18:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pixare', '0006_follow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='photo',
            name='square_loc',
        ),
    ]
