from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from core import const, factories

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        'название',
        max_length=const.MAX_INGREDIENT_NAME_LENGTH,
        unique=True,
        blank=False
    )

    measurement_unit = models.CharField(
        'единица измерения',
        max_length=const.MAX_MEASUREMENT_UNIT_LENGTH,
        blank=False
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return factories.make_model_str(self.name)


class Tag(models.Model):
    name = models.CharField(
        'название',
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
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return factories.make_model_str(self.name)


class Recipe(models.Model):
    name = models.CharField(
        'название',
        max_length=const.MAX_RECIPE_NAME_LENGTH
    )

    text = models.TextField('описание')

    image = models.ImageField(
        'картинка',
        upload_to='recipes',
        blank=False
    )

    cooking_time = models.SmallIntegerField(
        'время приготовления',
        help_text='минут',
        validators=(MinValueValidator(limit_value=1),)
    )

    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient'
    )

    tags = models.ManyToManyField(Tag)

    created_at = models.DateTimeField(
        'создано', auto_now_add=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)
        constraints = (
            models.CheckConstraint(name='positive_cooking_time',
                                   check=models.Q(cooking_time__gt=0)),
        )

    def __str__(self) -> str:
        return factories.make_model_str(self.name)


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='ингредиенты'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient'
    )

    amount = models.SmallIntegerField(
        'количество',
        validators=(MinValueValidator(limit_value=1),)
    )

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = (
            models.UniqueConstraint(fields=('ingredient', 'recipe'),
                                    name='unique_ingredient'),
            models.CheckConstraint(name='positive_amount',
                                   check=models.Q(amount__gt=0))
        )


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='рецепт'
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='unique_favorite'),
        )

    def __str__(self) -> str:
        return f'Запись в избранном <id: {self.pk}>'


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
        verbose_name = 'корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = (
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name=('shopping_cart_'
                                          'include_unique_recipes')),
        )

    def __str__(self) -> str:
        return factories.make_model_str(
            f'Запись в корзине покупок <id: {self.pk}>'
        )


class RecipeShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe, on_delete=models.CASCADE,
        related_name='link_token'
    )

    token = models.SlugField(
        max_length=const.MAX_SHORT_LINK_TOKEN_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'

    def __str__(self) -> str:
        return factories.make_model_str(
            f'Запись в коротких ссылках <id: {self.pk}>'
        )
