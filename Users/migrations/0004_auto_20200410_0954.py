# Generated by Django 3.0.4 on 2020-04-10 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0003_auto_20200329_1132'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='profile_pic_link',
        ),
        migrations.AddField(
            model_name='profile',
            name='pic_id',
            field=models.PositiveIntegerField(null=True),
        ),
    ]