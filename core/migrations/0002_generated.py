# Generated by Django 5.2.3 on 2025-06-23 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Generated',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playlist_name', models.CharField(max_length=255)),
                ('user_id', models.CharField(max_length=255)),
                ('themes', models.JSONField()),
            ],
        ),
    ]
