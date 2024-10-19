from typing import Any, Type

from django.db import transaction
from django.db.models import Model
from django.contrib.auth import get_user_model

import djoser.serializers as djoser_serializers

from drf_extra_fields.fields import Base64ImageField

from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request

import api.validators as api_validators
from foodgram import models
from users.models import MyUser

User = get_user_model()


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        extra_kwargs = {'first_name': {'required': True},
                        'last_name': {'required': True}}


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj: MyUser) -> bool:
        request: Request = self.context['request']
        if not request.auth:
            return False

        if not hasattr(self, 'user_follow'):
            self.user_follow = {author.pk for author
                                in request.user.subscriptions_set.all()}

        return obj.pk in self.user_follow


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')

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


class IngredientForRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1)
    amount = serializers.IntegerField(min_value=1)


class TagsIngredientsForRecipeSerialiser(serializers.Serializer):
    tags = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        validators=(api_validators.repetitions_id_validator,),
        allow_empty=False
    )

    ingredients = serializers.ListField(
        child=IngredientForRecipeSerializer(),
        validators=(api_validators.repetitions_id_validator,),
        allow_empty=False
    )

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

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        errors = {}
        for model in (models.Tag, models.Ingredient):
            self._validate_objects_exists(model, data, errors)

        if errors:
            raise ValidationError(errors)

        return data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredient',
                                             read_only=True)
    image = Base64ImageField(
        validators=(api_validators.empty_image_validator,)
    )

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        exclude = ('created_at',)

    def get_is_favorited(self, obj: models.Recipe) -> bool:
        request: Request = self.context['request']
        if not request.auth:
            return False

        if not hasattr(self, 'user_favorited'):
            self.user_favorited = {favorite.recipe_id for favorite
                                   in request.user.favorite.all()}

        return obj.pk in self.user_favorited

    def get_is_in_shopping_cart(self, obj: models.Recipe) -> bool:
        request: Request = self.context['request']
        if not request.auth:
            return False

        if not hasattr(self, 'user_shopping_cart'):
            self.user_shopping_cart = {item.recipe_id for item
                                       in request.user.shopping_cart.all()}

        return obj.pk in self.user_shopping_cart

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        errors = {}
        try:
            data.update(super().to_internal_value(data))
        except ValidationError as exc:
            errors = exc.detail

        tags_ingredients = TagsIngredientsForRecipeSerialiser(data=data)
        tags_ingredients.is_valid()
        errors.update(tags_ingredients.errors)

        if errors:
            raise ValidationError(errors)

        return data

    def create(self, validated_data: dict[str, Any]) -> models.Recipe:
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        try:
            with transaction.atomic():
                recipe = models.Recipe.objects.create(
                    author=self.context['request'].user, **validated_data
                )

                models.RecipeTag.objects.bulk_create(
                    (models.RecipeTag(recipe=recipe, tag_id=id)
                     for id in tags)
                )

                models.RecipeIngredient.objects.bulk_create(
                    (models.RecipeIngredient(
                        recipe=recipe,
                        ingredient_id=item['id'],
                        amount=item['amount']
                    )
                        for item in ingredients)
                )
        except Exception:
            raise APIException()

        return recipe

    def update(self, instance: models.Recipe,
               validated_data: dict[str, Any]) -> models.Recipe:
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        try:
            with transaction.atomic():
                models.Recipe.objects.filter(
                    pk=instance.pk
                ).update(**validated_data)

                models.RecipeTag.objects.filter(
                    recipe_id=instance.pk
                ).delete()
                models.RecipeIngredient.objects.filter(
                    recipe_id=instance.pk
                ).delete()

                models.RecipeTag.objects.bulk_create(
                    (models.RecipeTag(recipe_id=instance.pk, tag_id=id)
                     for id in tags)
                )

                models.RecipeIngredient.objects.bulk_create(
                    (models.RecipeIngredient(
                        recipe_id=instance.pk,
                        ingredient_id=item['id'],
                        amount=item['amount']
                    )
                        for item in ingredients)
                )
        except Exception:
            raise APIException()

        return models.Recipe.objects.get(pk=instance.pk)


class FavoriteAndShoppingCart(serializers.ModelSerializer):
    recipe_id = serializers.IntegerField(write_only=True, min_value=1)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Recipe
        create_model = Model
        fields = ('id', 'name', 'image', 'cooking_time', 'recipe_id', 'user')
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {'read_only': True},
            'image': {'read_only': True},
            'cooking_time': {'read_only': True}
        }

    def create(self, validated_data: dict[str, Any]):
        return self.Meta.create_model.objects.create(**validated_data).recipe


class FavoriteRecipeSerializer(FavoriteAndShoppingCart):
    class Meta(FavoriteAndShoppingCart.Meta):
        create_model = models.FavoriteRecipe


class ShoppingCartRecipeSerializer(FavoriteAndShoppingCart):
    class Meta(FavoriteAndShoppingCart.Meta):
        create_model = models.ShoppingCartRecipe
