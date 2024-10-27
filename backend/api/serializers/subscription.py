from typing import Union

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

from api.serializers.common import CommonRecipeReadSerializer
from api.serializers.user import UserReadSerializer
from users.models import Subscription
from users.models import User as UserType

User = get_user_model()


class SubscriptionSerializer(UserReadSerializer):
    user_id = serializers.IntegerField(write_only=True)
    author_id = serializers.IntegerField(write_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.ReadOnlyField(default=True)

    class Meta(UserReadSerializer.Meta):
        fields = (
            UserReadSerializer.Meta.fields
            + ('is_subscribed', 'recipes', 'recipes_count',
                'user_id', 'author_id')
        )
        read_only_fields = ('username', 'first_name',
                            'last_name', 'email', 'avatar')

    def validate(self, data):
        user_id = data['user_id']
        author_id = data['author_id']
        if user_id == author_id:
            raise ValidationError('Пользователь и автор совпадают.')

        if Subscription.objects.filter(
                user_id=user_id,
                author_id=author_id
        ).exists():
            raise ValidationError('Повторная подписка.')
        return data

    def get_recipes(self, author: UserType) -> Union[ReturnList, ReturnDict]:
        recipes_qs = author.recipes.all()
        request: Request = self.context['request']

        if ('recipes_limit' in request.query_params
                and request.query_params['recipes_limit'].isdigit()):
            limit = int(request.query_params['recipes_limit'])

            if limit > 0:
                recipes_qs = recipes_qs[:limit]

        return CommonRecipeReadSerializer(recipes_qs,
                                          many=True,
                                          context=self.context).data

    def create(self, validated_data):
        Subscription.objects.create(user_id=validated_data['user_id'],
                                    author_id=validated_data['author_id'])
        return validated_data['author']
