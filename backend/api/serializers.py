from users.models import MyUser
from foodgram.models import Ingredient, Recipe, RecipeIngredient, Tag
from typing import Any

from django.contrib.auth import get_user_model

import djoser.serializers as djoser_serializers

from drf_extra_fields.fields import Base64ImageField

from rest_framework.request import Request
from rest_framework import serializers


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
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
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
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredient',
                                             read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'

    # def is_favorited(self, obj: Recipe) -> bool:
    #     pass

    # def is_in_shopping_cart(self, obj: Recipe) -> bool:
        # pass

    def validate_tags(self, value):
        breakpoint()
        return value

    def validate_ingredients(self, value):
        breakpoint()
        return value

    def to_internal_value(self, data):
        breakpoint()
        ret = super().to_internal_value(data)
        # validate 'tags' key, check doubles, compare len input and queryset result
        ret['tags'] = Tag.objects.filter(pk__in=data['tags']).all()
        # check ingredients amounts > 0
        # validate 'ingredients' key, check doubles, compare len input and queryset result
        Ingredient.objects.filter(
            pk__in=(item['id'] for item in data['ingredients'])
        ).all()
        ret['ingredients'] = data['ingredients']
        return ret

    def create(self, validated_data: dict[str, Any]):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data)
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            (RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            )
                for item in ingredients))
        return recipe
