from django.contrib.auth import get_user_model
from django.db.models import Manager

from drf_extra_fields.fields import Base64ImageField

from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from foodgram.models import Ingredient
from users.models import MyUser

User = get_user_model()


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
