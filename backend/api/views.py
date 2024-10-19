from functools import partial
from typing import Type

from django.contrib.auth import get_user_model
from django.db.models import Model
from django.shortcuts import get_object_or_404

from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from api.filters import IngredientListFilter, RecipeListFilter
from api.permissions import IsOwnerAdminOrReadOnly
from api.serializers import (AvatarSerializer, FavoriteShoppingCartSerializer,
                             IngredientSerializer, RecipeSerializer,
                             SubscriptionSerializer, TagSerializer,)

from foodgram import models

from .const import LOOKUP_DIGIT_PATTERN, HttpMethod

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    http_method_names = [
        HttpMethod.GET,
        HttpMethod.POST,
        HttpMethod.PUT,
        HttpMethod.DELETE,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    ]
    lookup_value_regex = LOOKUP_DIGIT_PATTERN
    queryset = User.objects.all()

    def get_serializer_class(self) -> Type[ModelSerializer]:
        if self.action == 'avatar':
            return AvatarSerializer
        if (self.action == 'subscriptions'
                or self.action == 'subscribe'):
            return SubscriptionSerializer
        return super().get_serializer_class()

    @action([HttpMethod.GET],
            detail=False, permission_classes=[IsAuthenticated])
    def me(self, request: Request) -> Response:
        self.get_object = self.get_instance
        return self.retrieve(request)

    @action([HttpMethod.PUT, HttpMethod.DELETE],
            url_path='me/avatar',
            detail=False,
            permission_classes=[IsAuthenticated])
    def avatar(self, request: Request) -> Response:
        if request.method.lower() == HttpMethod.DELETE:
            request.user.avatar = None
            request.user.save(update_fields=('avatar',))
            return Response(status=status.HTTP_204_NO_CONTENT)
        self.get_object = self.get_instance
        return self.update(request)

    @action(methods=[HttpMethod.GET], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request: Request) -> Response:
        subs_qs = request.user.subscriptions_set.select_related('author').all()
        serializer = self.get_serializer(
            self.paginate_queryset([item.author for item in subs_qs]),
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action([HttpMethod.POST, HttpMethod.DELETE], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request: Request, id: str) -> Response:
        if request.user.id == int(id):
            raise ValidationError(
                {self.action: 'Пользователь и автор совпадают.'}
            )
        author = get_object_or_404(User, pk=id)
        subscription_qs = models.Subscription.objects.filter(user=request.user,
                                                             author=author)

        if request.method.lower() == HttpMethod.DELETE:
            if not subscription_qs:
                raise ValidationError({self.action: 'Подписка отсутствует.'})
            subscription_qs[0].delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if subscription_qs:
            raise ValidationError({self.action: 'Повторная подписка.'})

        models.Subscription.objects.create(user=request.user, author=author)
        return Response(self.get_serializer(author).data,
                        status=status.HTTP_201_CREATED)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = [
        HttpMethod.GET,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    ]
    queryset = models.Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientListFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names = [
        HttpMethod.GET,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    ]
    queryset = models.Tag.objects.all()
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
    lookup_url_kwarg = 'recipe_id'
    lookup_value_regex = LOOKUP_DIGIT_PATTERN
    queryset = models.Recipe.objects.select_related(
        'author'
    ).prefetch_related('tags')
    serializer_class = RecipeSerializer
    filterset_class = RecipeListFilter
    permission_classes = [IsAuthenticatedOrReadOnly,
                          partial(IsOwnerAdminOrReadOnly, 'author')]

    def add_to_fav_or_shop_cart(self, request: Request, recipe_id: str,
                                inter_model: Type[Model]) -> Response:
        recipe = get_object_or_404(models.Recipe.objects, pk=recipe_id)
        stored_obj_qs = inter_model.objects.filter(user=request.user,
                                                   recipe=recipe)

        if request.method.lower() == HttpMethod.DELETE:
            if not stored_obj_qs:
                raise ValidationError({self.action: 'Рецепт не был добавлен.'})
            stored_obj_qs[0].delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if stored_obj_qs:
            raise ValidationError({self.action: 'Рецепт уже добавлен.'})

        inter_model.objects.create(user=request.user, recipe=recipe)

        return Response(FavoriteShoppingCartSerializer(recipe).data,
                        status=status.HTTP_201_CREATED)

    @action([HttpMethod.POST, HttpMethod.DELETE], detail=True,
            permission_classes=[IsAuthenticatedOrReadOnly])
    def favorite(self, request: Request, recipe_id: str) -> Response:
        return self.add_to_fav_or_shop_cart(request, recipe_id,
                                            models.FavoriteRecipe)

    @action([HttpMethod.POST, HttpMethod.DELETE], detail=True,
            permission_classes=[IsAuthenticatedOrReadOnly])
    def shopping_cart(self, request: Request, recipe_id: str) -> Response:
        return self.add_to_fav_or_shop_cart(request, recipe_id,
                                            models.ShoppingCartRecipe)

    @action([HttpMethod.GET], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request: Request) -> Response:
        return Response(data={'info': 'IN DEV! Not implemented'},
                        status=status.HTTP_501_NOT_IMPLEMENTED)

    # @action(['get'], detail=True)
    # def get_link(self):
    #     pass
