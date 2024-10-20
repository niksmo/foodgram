from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from . import const
from . import utils

User = get_user_model()


class AbstractCreatedAt(models.Model):
    created_at = models.DateTimeField(
        'Создано', auto_now_add=True
    )

    class Meta:
        abstract = True


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=const.MAX_INGREDIENT_NAME_LENGTH,
        unique=True,
        blank=False
    )

    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=const.MAX_MEASUREMENT_UNIT_LENGTH,
        blank=False
    )

    class Meta:
        verbose_name = 'ингродиент'
        verbose_name_plural = 'Ингродиенты'

    def __str__(self) -> str:
        return utils.get_model_admin_name(self.name)


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=const.MAX_TAG_NAME_LENGTH,
        unique=True,
        blank=False
    )

    slug = models.SlugField(
        max_length=const.MAX_TAG_SLUG_LENGTH,
        unique=True,
        blank=False
    )

    class Meta:
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self) -> str:
        return utils.get_model_admin_name(self.name)


class Recipe(AbstractCreatedAt):
    name = models.CharField(
        'Название',
        max_length=const.MAX_RECIPE_NAME_LENGTH
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
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(name='positive_cooking_time',
                                   check=models.Q(cooking_time__gt=0))
        ]

    def __str__(self) -> str:
        return utils.get_model_admin_name(self.name)


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
            models.UniqueConstraint(fields=('ingredient', 'recipe'),
                                    name='unique_ingredient'),
            models.CheckConstraint(name='positive_amount',
                                   check=models.Q(amount__gt=0))
        ]


class RecipeTag(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipes'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='tags_set'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('tag', 'recipe'),
                                    name='unique_tag'),
        ]


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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='unique_favorite'),
        ]


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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name=('shopping_cart_'
                                          'include_unique_recipes')),
        ]


class Subscription(AbstractCreatedAt):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions_set'
    )

    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribers_set'
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscriptions'
            ),
            models.CheckConstraint(
                check=~models.Q(user__exact=models.F('author')),
                name='user_cant_follow_on_self')
        ]


class RecipeShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe, on_delete=models.CASCADE,
        related_name='link_token'
    )

    token = models.SlugField(
        max_length=const.MAX_SHORT_LINK_TOKEN_LENGTH,
        unique=True
    )
