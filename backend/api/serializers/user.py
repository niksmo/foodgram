from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.request import Request

from users.models import User as UserType

User = get_user_model()


class UserReadSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('is_subscribed', 'avatar')

    def get_is_subscribed(self, author: UserType) -> bool:
        request: Request = self.context['request']
        return (
            request
            and request.auth is not None
            and request.user.subscriptions.filter(author=author).exists()
        )


class UserAvatarSerializer(UserSerializer):
    avatar = Base64ImageField()

    class Meta(UserSerializer.Meta):
        fields = ('avatar',)
