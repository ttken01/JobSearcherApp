# Generated by Django 4.0.3 on 2022-04-19 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apply',
            name='CV',
            field=models.FileField(null=True, upload_to='applies/%Y/%m'),
        ),
    ]
