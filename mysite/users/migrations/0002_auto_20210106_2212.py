# Generated by Django 3.1.3 on 2021-01-06 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='image',
            field=models.ImageField(default='images/default-image.jpg', upload_to='profile_pics'),
        ),
    ]
