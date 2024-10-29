from typing import Any, Union

from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import QueryDict
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

from api.serializers.common import CommonRecipeReadSerializer
from api.serializers.user import UserReadSerializer
from users.models import Subscription
from users.models import User as UserType

User = get_user_model()


class SubscriptionSerializer(UserReadSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField()

    class Meta(UserReadSerializer.Meta):
        fields = (UserReadSerializer.Meta.fields
                  + ('is_subscribed', 'recipes', 'recipes_count'))

        read_only_fields = ('username', 'first_name',
                            'last_name', 'email', 'avatar')

    def get_recipes(self, instance: UserType) -> Union[ReturnList, ReturnDict]:
        recipes_qs = instance.recipes.all()
        query_params: QueryDict = self.context['request'].query_params

        try:
            if ('recipes_limit' in query_params
                    and (limit := int(query_params['recipes_limit']))):
                recipes_qs = recipes_qs[:limit]
        except ValueError:
            pass

        return CommonRecipeReadSerializer(recipes_qs,
                                          many=True,
                                          context=self.context).data


class SubscribeSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = ('author', 'user')
        validators = tuple()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = attrs['user']
        author = attrs['author']
        if user == author:
            raise ValidationError('Пользователь и автор совпадают.')

        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError('Повторная подписка.')
        return attrs

    def to_representation(
        self,
        instance: Subscription
    ) -> Union[ReturnList, ReturnDict]:
        return SubscriptionSerializer(
            User.objects.filter(
                pk=instance.author.pk
            ).annotate(recipes_count=Count('recipes')).get(),
            context=self.context
        ).data
