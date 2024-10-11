from djoser.serializers import UserSerializer as DjoserUserSerializer

from drf_extra_fields.fields import Base64ImageField


class UserSerializer(DjoserUserSerializer):
    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('avatar',)
        read_only_fields = ('avatar',)


class AvatarSerializer(DjoserUserSerializer):
    avatar = Base64ImageField()

    class Meta(DjoserUserSerializer.Meta):
        fields = ('avatar',)
