# Generated by Django 4.2.16 on 2024-10-20 11:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodgram', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeShortLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.SlugField(max_length=8, unique=True)),
                ('recipe', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='short_link', to='foodgram.recipe')),
            ],
        ),
    ]
