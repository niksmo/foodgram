from secrets import token_urlsafe
from typing import Any, Iterable

from django.contrib.auth import get_user_model
from django.db.models import Manager
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from api.serializers.tag import TagSerializer
from api.serializers.user import UserReadSerializer
from core.const import (MIN_AMOUNT_VALUE, SHORT_LINK_SLUG_NBYTES,
                        SMALL_INTEGER_FIELD_MAX_VALUE)
from foodgram.models import (Ingredient, Recipe, RecipeIngredient,
                             RecipeShortLink, Tag)

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

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('created_at',)

    def get_is_favorited(self, obj: Recipe) -> bool:
        if 'request' not in self.context:
            return False

        request: Request = self.context['request']
        if not request.auth:
            return False

        if not hasattr(self, '_user_favorited'):
            self._user_favorited = {favorite.recipe_id for favorite
                                    in request.user.favorite_set.all()}

        return obj.pk in self._user_favorited

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        if 'request' not in self.context:
            return False

        request: Request = self.context['request']
        if not request.auth:
            return False

        if not hasattr(self, '_user_shopping_cart'):
            self._user_shopping_cart = {item.recipe_id for item
                                        in request.user.shoppingcart_set.all()}

        return obj.pk in self._user_shopping_cart


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

    class Meta:
        model = Recipe
        exclude = ('created_at',)
        read_only_fields = ('author',)

    def validate_image(self, value):
        if not value:
            raise ValidationError('Это поле не может быть пустым.')
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        errors = {}

        self._verify_repetition(
            'tags',
            (item.id for item in attrs['tags']),
            errors
        )

        self._verify_repetition(
            'ingredients',
            (item['id'].id for item in attrs['ingredients']),
            errors
        )

        if errors:
            raise ValidationError(errors)

        return attrs

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

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

    def _verify_repetition(self, field_name: str, ids: Iterable[int],
                           errors: dict[str, Any]) -> list[int]:
        doubles_set: set[int] = set()
        unique_set: set[int] = set()
        for id in ids:
            if id in unique_set:
                doubles_set.add(id)
            else:
                unique_set.add(id)

        if doubles_set:
            errors[field_name] = [
                {
                    'id': [
                        f'{field_name} с ID {sorted(doubles_set)} дублируются.'
                    ]
                }
            ]
        return sorted(unique_set)


class ShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeShortLink
        fields = '__all__'
        read_only_fields = ('slug',)
        extra_kwargs = {
            'recipe': {'write_only': True}
        }

    def create(self, validated_data):
        while True:
            slug = token_urlsafe(SHORT_LINK_SLUG_NBYTES)
            if not RecipeShortLink.objects.filter(slug=slug).exists():
                break
        return RecipeShortLink.objects.create(
            recipe=validated_data['recipe'],
            slug=slug
        )
