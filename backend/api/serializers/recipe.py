from secrets import token_urlsafe
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Exists, Manager, OuterRef
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.serializers.tag import TagSerializer
from api.serializers.user import UserReadSerializer
from core.const import (MIN_AMOUNT_VALUE, SHORT_LINK_SLUG_NBYTES,
                        SHORT_LINK_URL_PATH, SMALL_INTEGER_FIELD_MAX_VALUE)
from foodgram.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                             RecipeShortLink, ShoppingCart, Tag)

User = get_user_model()


class IngredientReadListSerializer(serializers.ListSerializer):
    """Special serializer for reduce database queries."""

    def to_representation(self, data: Manager):
        items = data.select_related('ingredient').all()

        return [
            self.child.to_representation(item) for item in items
        ]


class IngredientReadSerializer(serializers.ModelSerializer):
    """Special serializer for representation RecipeIngredients."""

    id = serializers.IntegerField(source='ingredient.id')

    name = serializers.ReadOnlyField(source='ingredient.name',
                                     read_only=True)

    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        list_serializer_class = IngredientReadListSerializer
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Special serializer for representation RecipeSerializer."""

    tags = TagSerializer(many=True)
    ingredients = IngredientReadSerializer(source='recipeingredient_set',
                                           many=True)
    author = UserReadSerializer()

    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        exclude = ('created_at',)


class IngredientCreateUpdateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects
    )

    amount = serializers.IntegerField(min_value=MIN_AMOUNT_VALUE,
                                      max_value=SMALL_INTEGER_FIELD_MAX_VALUE)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        allow_empty=False,
        queryset=Tag.objects.all()
    )

    ingredients = IngredientCreateUpdateSerializer(write_only=True,
                                                   many=True,
                                                   allow_empty=False)

    image = Base64ImageField()

    default_error_messages = {'doubles': '{} дублируются.'}

    class Meta:
        model = Recipe
        exclude = ('created_at',)
        read_only_fields = ('author',)

    def validate_image(self, value):
        if not value:
            raise ValidationError(self.error_messages['null'])
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        errors = {}

        if 'tags' not in attrs:
            errors.update(tags=[self.error_messages['required']])
        elif len(attrs['tags']) > len(set(attrs['tags'])):
            errors.update(tags=[
                self.default_error_messages['doubles'].format('Теги')
            ])

        if 'ingredients' not in attrs:
            errors.update(ingredients=[self.error_messages['required']])
        elif (len(attrs['ingredients'])
              > len(set(item['id'] for item in attrs['ingredients']))):
            errors.update(ingredients=[
                self.default_error_messages['doubles'].format('Ингредиенты')
            ])

        if errors:
            raise ValidationError(errors)

        return attrs

    def to_representation(self, instance):
        user = self.context['request'].user
        return RecipeReadSerializer(
            Recipe.objects.select_related(
                'author'
            ).prefetch_related(
                'tags'
            ).annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    recipe=OuterRef('pk'),
                    user=user
                )),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    recipe=OuterRef('pk'),
                    user=user
                ))
            ).get(pk=instance.pk),
            context=self.context
        ).data

    def create(self, validated_data: dict[str, Any]) -> Recipe:
        ingredients = validated_data.pop('ingredients')
        validated_data.update(author=self.context['request'].user)
        recipe: Recipe = super().create(validated_data)
        self._set_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance: Recipe,
               validated_data: dict[str, Any]) -> Recipe:
        ingredients = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self._set_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def _set_ingredients(self, recipe: Recipe, ingredients) -> None:
        RecipeIngredient.objects.bulk_create(
            (RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
                for item in ingredients)
        )


class ShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeShortLink
        fields = '__all__'
        read_only_fields = ('slug',)
        extra_kwargs = {
            'recipe': {'write_only': True,
                       'validators': None}
        }

    def to_representation(self, instance: RecipeShortLink):
        return {
            'short-link': self.context['request'].build_absolute_uri(
                f'/{SHORT_LINK_URL_PATH}{instance.slug}'
            )
        }

    def create(self, validated_data: dict[str, Any]):
        recipe = validated_data['recipe']
        try:
            instance = recipe.link_slug
        except RecipeShortLink.DoesNotExist:
            while True:
                slug = token_urlsafe(SHORT_LINK_SLUG_NBYTES)
                if not RecipeShortLink.objects.filter(slug=slug).exists():
                    break
            instance = RecipeShortLink.objects.create(recipe=recipe,
                                                      slug=slug)
        return instance
