from typing import Any, NoReturn, Type

from django.contrib.auth import get_user_model
from django.db.models import Manager, Model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.request import Request

from api.serializers.tag import TagSerializer
from api.serializers.user import UserReadSerializer
from api.validators import RecipeCreateUpdateValidator, empty_image_validator
from core.const import SMALL_INTEGER_FIELD_MAX_VALUE
from foodgram import models

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
        model = models.RecipeIngredient
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
        model = models.Recipe
        exclude = ('created_at',)

    def get_is_favorited(self, obj: models.Recipe) -> bool:
        if 'request' not in self.context:
            return False

        request: Request = self.context['request']
        if not request.auth:
            return False

        if not hasattr(self, '_user_favorited'):
            self._user_favorited = {favorite.recipe_id for favorite
                                    in request.user.favorite_set.all()}

        return obj.pk in self._user_favorited

    def get_is_in_shopping_cart(self, obj: models.Recipe) -> bool:
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
    id = serializers.IntegerField(min_value=1,
                                  source='ingredient_id')

    amount = serializers.IntegerField(min_value=1,
                                      max_value=SMALL_INTEGER_FIELD_MAX_VALUE)


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=models.Tag.objects.all()
    )

    ingredients = IngredientCreateUpdateSerializer(
        many=True, source='recipeingredient_set')

    image = Base64ImageField(validators=(empty_image_validator,))

    class Meta:
        model = models.Recipe
        exclude = ('created_at',)
        read_only_fields = ('author',)
        validators = (RecipeCreateUpdateValidator(),)

    def _validate_objects_exists(self, model: Type[Model],
                                 data: dict[str, Any],
                                 errors: dict[str, Any]) -> None:
        values = data[(field := f'{model.__name__.lower()}s')]

        if isinstance(values[0], dict):
            values = [item['id'] for item in values]

        exists_list = model.objects.filter(pk__in=values).all()

        if len(exists_list) != len(values):
            exists_pk_set = {instance.pk for instance in exists_list}
            not_exists = tuple(pk
                               for pk in values
                               if pk not in exists_pk_set)

            errors[field] = (f'{model.__name__} c "id" '
                             f'{sorted(not_exists)} '
                             'не существует.')

    def create(self, validated_data: dict[str, Any]) -> models.Recipe:
        ingredients = validated_data.pop('recipeingredient_set')
        recipe = super().create(validated_data)
        self._set_ingredients(recipe, ingredients)
        return recipe

    def _set_ingredients(self, recipe, ingredients) -> None:
        models.RecipeIngredient.objects.bulk_create(
            (models.RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['ingredient_id'],
                amount=item['amount']
            )
                for item in ingredients)
        )


class RecipeUpdateSerializer(RecipeCreateSerializer):
    image = Base64ImageField(required=False,
                             validators=(empty_image_validator,))

    def create(self, validated_data: dict[str, Any]) -> NoReturn:
        raise NotImplementedError()

    def update(self, recipe: models.Recipe,
               validated_data: dict[str, Any]) -> models.Recipe:
        ingredients = validated_data.pop('recipeingredient_set')

        recipe = super().update(recipe, validated_data)
        models.RecipeIngredient.objects.filter(recipe=recipe).delete()
        self._set_ingredients(recipe, ingredients)

        return recipe
