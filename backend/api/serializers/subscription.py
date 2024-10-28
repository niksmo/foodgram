from typing import Union

from django.contrib.auth import get_user_model
from django.db.models import Count
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
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.annotate(recipes_count=Count('recipes')),
        write_only=True
    )
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.ReadOnlyField(default=True)

    class Meta(UserReadSerializer.Meta):
        fields = (
            UserReadSerializer.Meta.fields
            + ('is_subscribed', 'recipes', 'recipes_count', 'author')
        )
        read_only_fields = ('username', 'first_name',
                            'last_name', 'email', 'avatar')

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']
        if user == author:
            raise ValidationError('Пользователь и автор совпадают.')

        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError('Повторная подписка.')
        return data

    def get_recipes(self, instance: UserType) -> Union[ReturnList, ReturnDict]:
        recipes_qs = instance.recipes.all()
        request: Request = self.context['request']

        if ('recipes_limit' in request.query_params
                and request.query_params['recipes_limit'].isdigit()):
            limit = int(request.query_params['recipes_limit'])

            if limit > 0:
                recipes_qs = recipes_qs[:limit]

        return CommonRecipeReadSerializer(recipes_qs,
                                          many=True,
                                          context=self.context).data

    def create(self, validated_data) -> UserType:
        author = validated_data['author']
        Subscription.objects.create(user=self.context['request'].user,
                                    author=author)
        return author
