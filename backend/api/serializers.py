from typing import Any, Type, Union

import djoser.serializers as djoser_serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Manager, Model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request

from api.validators import empty_image_validator, repetitions_id_validator
from foodgram import models
from users.models import MyUser

User = get_user_model()


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, author: MyUser) -> bool:
        if 'request' not in self.context:
            return False

        request: Request = self.context['request']
        if not request.auth or request.user == author:
            return False

        if not hasattr(self, '_subs_authors_id'):
            self._subs_authors_id = {
                sub.author_id for sub
                in request.user.subscriptions_set.all()
            }

        return author.pk in self._subs_authors_id


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = '__all__'


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Special serializer for representation RecipeIngredients."""

    id = serializers.IntegerField(
        source='ingredient.id'
    )

    name = serializers.ReadOnlyField(
        source='ingredient.name',
        read_only=True
    )

    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientListReadSerializer(serializers.ListSerializer):
    """Special serializer for reduce database queries."""

    def to_representation(self, data: Manager):
        items = data.select_related('ingredient').all()

        return [
            self.child.to_representation(item) for item in items
        ]


class RecipeReadSerializer(serializers.ModelSerializer):
    """Special serializer for representation RecipeSerializer."""

    tags = TagSerializer(many=True)
    author = UserReadSerializer()
    ingredients = RecipeIngredientListReadSerializer(
        child=RecipeIngredientReadSerializer(),
        source='recipe_ingredient'
    )

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

        if not hasattr(self, 'user_favorited'):
            self.user_favorited = {favorite.recipe_id for favorite
                                   in request.user.favorite.all()}

        return obj.pk in self.user_favorited

    def get_is_in_shopping_cart(self, obj: models.Recipe) -> bool:
        if 'request' not in self.context:
            return False

        request: Request = self.context['request']
        if not request.auth:
            return False

        if not hasattr(self, 'user_shopping_cart'):
            self.user_shopping_cart = {item.recipe_id for item
                                       in request.user.shopping_cart.all()}

        return obj.pk in self.user_shopping_cart


class RecipeIngredientCreateUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1)
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.IntegerField(
            min_value=1,
        ),
        allow_empty=False,
        validators=(repetitions_id_validator,),
    )

    ingredients = serializers.ListField(
        child=RecipeIngredientCreateUpdateSerializer(),
        allow_empty=False,
        validators=(repetitions_id_validator,))

    image = Base64ImageField(validators=(empty_image_validator,))

    class Meta:
        model = models.Recipe
        exclude = ('created_at',)
        read_only_fields = ('author',)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        errors = {}
        for model in (models.Tag, models.Ingredient):
            self._validate_objects_exists(model, data, errors)
        if errors:
            raise ValidationError(errors)
        return data

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

    def to_representation(self, recipe: models.Recipe):
        return RecipeReadSerializer(recipe, context=self.context).data

    def create(self, validated_data: dict[str, Any]) -> models.Recipe:
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        try:
            with transaction.atomic():
                recipe = models.Recipe.objects.create(**validated_data)
                self._set_tags_ingredients(recipe, tags, ingredients)
        except Exception:
            raise APIException()

        return recipe

    def _set_tags_ingredients(self, recipe, tags, ingredients) -> None:
        models.RecipeTag.objects.bulk_create(
            (models.RecipeTag(recipe=recipe, tag_id=id) for id in tags)
        )

        models.RecipeIngredient.objects.bulk_create(
            (models.RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            )
                for item in ingredients)
        )


class RecipeUpdateSerializer(RecipeCreateSerializer):

    image = Base64ImageField(required=False)

    def update(self, recipe: models.Recipe,
               validated_data: dict[str, Any]) -> models.Recipe:
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        try:
            with transaction.atomic():
                super().update(recipe, validated_data)
                for model in (models.RecipeTag, models.RecipeIngredient):
                    model.objects.filter(recipe=recipe).delete()
                self._set_tags_ingredients(recipe, tags, ingredients)
        except Exception:
            raise APIException()

        return recipe


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionReadRecipeSerialiser(serializers.ModelSerializer):
    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.ReadOnlyField(default=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def produce_recipe_limit(self) -> Union[int, None]:
        request: Request = self.context['request']
        if 'recipes_limit' not in request.query_params:
            return None

        limit_str: str = request.query_params['recipes_limit']
        assert limit_str.isdigit(), 'Expected limit is converting to `int`'
        limit = int(limit_str)
        assert limit > 0, 'Expected limit more then `0`'

        return limit

    def get_recipes(self, author: MyUser):
        recipes = author.recipes.all()
        self.context['recipes_count'] = len(recipes)
        return [
            SubscriptionReadRecipeSerialiser(recipe, context=self.context).data
            for recipe in recipes
        ][0:self.produce_recipe_limit()]

    def get_recipes_count(self, _: MyUser):
        assert 'recipes_count' in self.context, (
            '`recipes_count` '
            'should being after `recipes` in `self.Meta.fields`'
        )
        return self.context['recipes_count']

    def to_internal_value(self, data):
        raise NotImplementedError(
            'Unnecessary method which may cause unexpected behavior.'
        )
