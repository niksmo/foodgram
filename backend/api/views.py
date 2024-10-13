from django.contrib.auth import get_user_model

from djoser.conf import settings
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self) -> ModelSerializer:
        if self.action == 'avatar':
            return settings.SERIALIZERS.avatar
        return super().get_serializer_class()

    @action(['get'],
            detail=False, permission_classes=[IsAuthenticated])
    def me(self, request: Request, *args, **kwargs) -> Response:
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(['put', 'delete'],
            url_path='me/avatar',
            detail=False,
            permission_classes=[IsAuthenticated])
    def avatar(self, request: Request, *args, **kwargs) -> Response:
        if request.method and request.method.lower() == 'delete':
            request.user.avatar = None
            request.user.save(update_fields=('avatar',))
            return Response(status=204)
        self.get_object = self.get_instance
        return self.partial_update(request, *args, **kwargs)
