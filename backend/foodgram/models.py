from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=128,
        unique=True,
        blank=False
    )

    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64,
        blank=False
    )

    class Meta:
        pass


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=32,
        unique=True,
        blank=False
    )

    slug = models.SlugField(
        max_length=32,
        unique=True,
        blank=False
    )

    class Meta:
        pass


class Recipe(models.Model):
    name = models.CharField(
        'Название',
        max_length=256
    )

    text = models.TextField('Описание')

    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        blank=False
    )

    cooking_time = models.SmallIntegerField(
        'Время приготовления',
        help_text='минут',
        validators=[MinValueValidator(limit_value=1)]
    )

    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient'
    )

    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag'
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='positive_cooking_time',
                check=models.Q(cooking_time__gt=0)
            )
        ]


class MyQeurySet(models.QuerySet):
    def objects(self):
        return self.select_related('ingredient')


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient'
    )

    amount = models.SmallIntegerField(
        'Количество',
        validators=[MinValueValidator(limit_value=1)]
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='positive_amount',
                check=models.Q(amount__gt=0)
            )
        ]


class RecipeTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorites'
    )


class ShoppingCartRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_carts'
    )
