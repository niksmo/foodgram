# Generated by Django 4.2.16 on 2024-10-14 21:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodgram', '0003_recipe_tagrecipe_recipeingredient_recipe_ingredients_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tag',
            name='recipes',
        ),
    ]
