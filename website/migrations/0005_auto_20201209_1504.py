# Generated by Django 3.1.2 on 2020-12-09 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_auto_20201209_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='first_name',
            field=models.CharField(default=None, max_length=30, verbose_name='first_name'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='last_name',
            field=models.CharField(default=None, max_length=30, verbose_name='last_name'),
        ),
    ]