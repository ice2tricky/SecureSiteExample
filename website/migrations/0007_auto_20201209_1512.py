# Generated by Django 3.1.2 on 2020-12-09 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0006_auto_20201209_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='first_name',
            field=models.CharField(default='tes', max_length=30, verbose_name='first_name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profile',
            name='last_name',
            field=models.CharField(default='ter', max_length=30, verbose_name='last_name'),
            preserve_default=False,
        ),
    ]
