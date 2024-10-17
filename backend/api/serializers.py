from typing import Any, Type

from django.db.models import Model
from django.contrib.auth import get_user_model

import djoser.serializers as djoser_serializers

from drf_extra_fields.fields import Base64ImageField

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError

import api.validators as api_validators
import foodgram.models as fg_models
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
            self.user_follow = {author.pk
                                for author in request.user.follow.all()}

        return obj.pk in self.user_follow


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = fg_models.Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = fg_models.Tag
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
        model = fg_models.RecipeIngredient
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

    def _validate_objects_exists(self,
                                 model: Type[Model],
                                 data: dict[str, Any],
                                 errors: dict[str, Any]):
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

    def validate(self, data: dict[str, Any]):
        errors = {}
        for model in (fg_models.Tag, fg_models.Ingredient):
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

    class Meta:
        model = fg_models.Recipe
        fields = '__all__'

    # def is_favorited(self, obj: Recipe) -> bool:
    #     pass

    # def is_in_shopping_cart(self, obj: Recipe) -> bool:
        # pass

    def to_internal_value(self, data: dict[str, Any]):
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

    def create(self, validated_data: dict[str, Any]):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = fg_models.Recipe.objects.create(
            author=self.context['request'].user, **validated_data)

        fg_models.RecipeTag.objects.bulk_create(
            (fg_models.RecipeTag(recipe=recipe, tag_id=id)
             for id in tags)
        )

        fg_models.RecipeIngredient.objects.bulk_create(
            (fg_models.RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            )
                for item in ingredients)
        )
        return recipe
