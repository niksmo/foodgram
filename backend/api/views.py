from dataclasses import dataclass
from typing import Type
from functools import partial

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

import django_filters

from djoser.conf import settings
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework import exceptions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer

from api.filters import IngredientListFilter
from api.permissions import IsOwnerAdminOrReadOnly
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             TagSerializer, FavoriteRecipeSerializer)

import foodgram.models as fg_models

User = get_user_model()


@dataclass(frozen=True)
class HttpMethod:
    GET = 'get'
    POST = 'post'
    DELETE = 'delete'
    PUT = 'put'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'


class UserViewSet(DjoserUserViewSet):
    http_method_names = [
        HttpMethod.GET,
        HttpMethod.POST,
        HttpMethod.PUT,
        HttpMethod.DELETE,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    ]
    queryset = User.objects.all()

    def get_serializer_class(self) -> Type[ModelSerializer]:
        if self.action == 'avatar':
            return settings.SERIALIZERS.avatar
        return super().get_serializer_class()

    @action([HttpMethod.GET],
            detail=False, permission_classes=[IsAuthenticated])
    def me(self, request: Request, *args, **kwargs) -> Response:
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action([HttpMethod.PUT, HttpMethod.DELETE],
            url_path='me/avatar',
            detail=False,
            permission_classes=[IsAuthenticated])
    def avatar(self, request: Request, *args, **kwargs) -> Response:
        if request.method and request.method.lower() == HttpMethod.DELETE:
            request.user.avatar = None
            request.user.save(update_fields=('avatar',))
            return Response(status=status.HTTP_204_NO_CONTENT)
        self.get_object = self.get_instance
        return self.update(request, *args, **kwargs)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = [
        HttpMethod.GET,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    ]
    queryset = fg_models.Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = IngredientListFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = [
        HttpMethod.GET,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    ]
    queryset = fg_models.Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = [
        HttpMethod.GET,
        HttpMethod.POST,
        HttpMethod.PATCH,
        HttpMethod.DELETE,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    ]
    queryset = fg_models.Recipe.objects.select_related(
        'author'
    ).prefetch_related('tags')
    serializer_class = RecipeSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    permission_classes = [IsAuthenticatedOrReadOnly,
                          partial(IsOwnerAdminOrReadOnly, 'author')]

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == 'favorite':
            return FavoriteRecipeSerializer
        return super().get_serializer_class()

    # @action(['get'], detail=True)
    # def get_link(self):
    #     pass

    @action([HttpMethod.POST, HttpMethod.DELETE],
            detail=True,
            permission_classes=[IsAuthenticatedOrReadOnly,
                                partial(IsOwnerAdminOrReadOnly, 'user')])
    def favorite(self, request: Request, pk: str) -> Response:
        if request.method and request.method.lower() == HttpMethod.DELETE:
            recipe = get_object_or_404(fg_models.Recipe.objects, pk=pk)
            try:
                favorite_recipe = recipe.in_favorites.get(user=request.user)
            except ObjectDoesNotExist:
                raise exceptions.ValidationError(
                    'Рецепт не был добавлен в избранное.'
                )

            self.check_object_permissions(self.request, favorite_recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer: Serializer = self.get_serializer(data={'recipe_id': pk})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)
