from typing import Union

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

from api.serializers.user import UserReadSerializer
from foodgram.models import Recipe
from users.models import Subscription
from users.models import User as UserType

User = get_user_model()


class SubscriptionReadRecipeSerialiser(serializers.ModelSerializer):
    # RETURN HERE AFTER RECIPE
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserReadSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.ReadOnlyField(default=True)

    class Meta(UserReadSerializer.Meta):
        fields = (UserReadSerializer.Meta.fields
                  + ('is_subscribed', 'recipes', 'recipes_count'))
        read_only_fields = ('username', 'first_name', 'last_name',
                            'email', 'avatar')

    def validate(self, data):
        if self.context['request'].user.id == self.initial_data['id']:
            raise ValidationError('Пользователь и автор совпадают.')
        return data

    def get_recipes(self, author: UserType) -> Union[ReturnList, ReturnDict]:
        recipes_qs = author.recipes.all()
        request: Request = self.context['request']

        if ('recipes_limit' in request.query_params
                and request.query_params['recipes_limit'].isdigit()):
            limit = int(request.query_params['recipes_limit'])

            if limit > 0:
                recipes_qs = recipes_qs[:limit]

        return SubscriptionReadRecipeSerialiser(recipes_qs,
                                                many=True,
                                                context=self.context).data

    def create(self, validated_data):
        author = validated_data.pop('author')
        Subscription.objects.create(
            user_id=validated_data['user_id'],
            author_id=author.id
        )
        return author
