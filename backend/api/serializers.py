from django.contrib.auth import get_user_model

import djoser.serializers as djoser_serializers

from drf_extra_fields.fields import Base64ImageField

from rest_framework.request import Request
from rest_framework.serializers import (ModelSerializer, SerializerMethodField,
                                        IntegerField, ReadOnlyField)

from foodgram.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import MyUser

User = get_user_model()


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        extra_kwargs = {'first_name': {'required': True},
                        'last_name': {'required': True}}


class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj: MyUser):
        request: Request = self.context['request']
        if not request.auth:
            return False

        if not hasattr(self, 'user_follow'):
            self.user_follow = {author.pk
                                for author in request.user.follow.all()}

        return obj.pk in self.user_follow


class AvatarSerializer(ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(ModelSerializer):
    id = IntegerField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredient')
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'
