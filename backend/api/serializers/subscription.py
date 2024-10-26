from typing import Union

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.request import Request

from foodgram import models
from users.models import MyUser

User = get_user_model()


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
