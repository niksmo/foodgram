from django.contrib.auth import get_user_model

from drf_extra_fields.fields import Base64ImageField

from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from users.models import MyUser

User = get_user_model()


class UserSerializer(ModelSerializer):

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, user_instance: MyUser):
        request: Request = self.context['request']
        if not request.auth:
            return False

        return user_instance.followers.filter(
            pk=request.user.id
        ).exists()


class AvatarSerializer(ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
