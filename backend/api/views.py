from django.contrib.auth import get_user_model

import django_filters

import django_filters.fields
from djoser.conf import settings
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from foodgram.models import Ingredient, Tag
from api.serializers import IngredientSerializer, TagSerializer
from api.filters import IngredientListFilter

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
        return self.update(request, *args, **kwargs)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = IngredientListFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
