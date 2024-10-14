from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField('Название',
                            max_length=128,
                            unique=True,
                            blank=False)

    measurement_unit = models.CharField('Единица измерения',
                                        max_length=64,
                                        blank=False)

    class Meta:
        pass


class Tag(models.Model):
    name = models.CharField('Название',
                            max_length=32,
                            unique=True,
                            blank=False)

    slug = models.SlugField(max_length=32,
                            unique=True,
                            blank=False)

    class Meta:
        pass


class Recipe(models.Model):
    name = models.CharField('Название',
                            max_length=256)

    text = models.TextField('Описание')

    image = models.ImageField('Картинка',
                              upload_to='recipes/')

    cooking_time = models.SmallIntegerField('Время приголовления',
                                            help_text='минут')

    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE)

    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')

    tags = models.ManyToManyField(Tag,
                                  through='TagRecipe')

    class Meta:
        constraints = [
            models.CheckConstraint(name='positive_cooking_time',
                                   check=models.Q(cooking_time__gt=0))
        ]


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.SmallIntegerField('Количество')

    class Meta:
        constraints = [
            models.CheckConstraint(name='positive_amount',
                                   check=models.Q(amount__gt=0))
        ]


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
