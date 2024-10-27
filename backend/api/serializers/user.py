import djoser.serializers as djoser_serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.request import Request

from users.models import User as UserType

User = get_user_model()


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, author: UserType) -> bool:
        if 'request' not in self.context:
            return False

        request: Request = self.context['request']
        if not request.auth or request.user == author:
            return False

        if not hasattr(self, '_subs_authors_id'):
            self._subs_authors_id = {
                sub.author_id for sub
                in request.user.subscriptions.all()
            }

        return author.pk in self._subs_authors_id


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
