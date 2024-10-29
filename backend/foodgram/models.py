from typing import Optional

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef, Value

from core import const, factories

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(const.VERBOSE_NAME_FIELD,
                            max_length=const.MAX_INGREDIENT_NAME_LENGTH,
                            unique=True)

    measurement_unit = models.CharField(
        'единица измерения',
        max_length=const.MAX_MEASUREMENT_UNIT_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = const.VERBOSE_INGREDIENT_FIELD
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(fields=('name', 'measurement_unit'),
                                    name='only_one_unit_for_ingredient'),
        )

    def __str__(self) -> str:
        return factories.make_model_str(self.name)


class Tag(models.Model):
    name = models.CharField(const.VERBOSE_NAME_FIELD,
                            max_length=const.MAX_TAG_NAME_LENGTH,
                            unique=True)

    slug = models.SlugField(const.VERBOSE_SLUG_FIELD,
                            max_length=const.MAX_SLUG_LENGTH,
                            unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return factories.make_model_str(self.name)


class UserRecipeIntermediateAbstract(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='пользователь')

    recipe = models.ForeignKey('Recipe',
                               on_delete=models.CASCADE,
                               verbose_name=const.VERBOSE_RECIPE_FIELD)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return factories.make_model_str(
            f'Пользователь-{self._meta.verbose_name} <id: {self.pk}'
        )


class Favorite(UserRecipeIntermediateAbstract):
    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='favorite:user_recipe_unique_together'
            ),
        )


class ShoppingCart(UserRecipeIntermediateAbstract):
    class Meta:
        verbose_name = 'корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='shopping_cart:user_recipe_unique_together'
            ),
        )


class RecipeQuerySet(models.QuerySet):
    def annotate_is_favorited_in_shopping_cart(
        self, *,
        user_id: Optional[int] = None
    ) -> models.QuerySet:
        is_favorited = Value(False)
        is_in_shopping_cart = Value(False)
        if user_id:
            is_favorited = Exists(
                Favorite.objects.filter(recipe=OuterRef('pk'),
                                        user_id=user_id)
            )
            is_in_shopping_cart = Exists(
                ShoppingCart.objects.filter(recipe=OuterRef('pk'),
                                            user_id=user_id)
            )
        return self.annotate(is_favorited=is_favorited,
                             is_in_shopping_cart=is_in_shopping_cart)


class Recipe(models.Model):
    name = models.CharField(const.VERBOSE_NAME_FIELD,
                            max_length=const.MAX_RECIPE_NAME_LENGTH)

    text = models.TextField('описание')

    image = models.ImageField('картинка', upload_to='recipes')

    cooking_time = models.PositiveSmallIntegerField(
        'время приготовления',
        help_text='минут',
        validators=(
            MinValueValidator(limit_value=const.MIN_COOKING_TIME_VALUE),
            MaxValueValidator(limit_value=const.SMALL_INTEGER_FIELD_MAX_VALUE)
        )
    )

    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE,
                               verbose_name='автор')

    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         verbose_name='ингредиенты')

    tags = models.ManyToManyField(Tag, verbose_name='теги')

    created_at = models.DateTimeField('создан', auto_now_add=True)

    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = const.VERBOSE_RECIPE_FIELD
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return factories.make_model_str(self.name)


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   verbose_name=const.VERBOSE_INGREDIENT_FIELD)

    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name=const.VERBOSE_RECIPE_FIELD)

    amount = models.PositiveSmallIntegerField(
        'количество',
        validators=(
            MinValueValidator(limit_value=const.MIN_AMOUNT_VALUE),
            MaxValueValidator(limit_value=const.SMALL_INTEGER_FIELD_MAX_VALUE)
        )
    )

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = (
            models.UniqueConstraint(fields=('ingredient', 'recipe'),
                                    name='unique_ingredient'),
        )

    def __str__(self) -> str:
        return factories.make_model_str(f'Ингредиент-рецепт <id: {self.pk}>')


class RecipeShortLink(models.Model):
    recipe = models.OneToOneField(Recipe,
                                  on_delete=models.CASCADE,
                                  related_name='link_slug',
                                  verbose_name=const.VERBOSE_RECIPE_FIELD)

    slug = models.SlugField(const.VERBOSE_SLUG_FIELD,
                            max_length=const.MAX_SLUG_LENGTH,
                            unique=True)

    class Meta:
        verbose_name = 'короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'

    def __str__(self) -> str:
        return factories.make_model_str(
            f'Рецепт-ссылка <id: {self.pk}>'
        )
