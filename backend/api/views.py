from typing import Type

from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, F, Model, OuterRef, Sum, Value
from django.http.response import FileResponse, HttpResponseBase
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from api.filters import IngredientListFilter, RecipeListFilter
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeReadSerializer, ShoppingCartSerializer,
                             ShortLinkSerializer, SubscribeSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserAvatarSerializer)
from core.const import LOOKUP_DIGIT_PATTERN, HttpMethod
from core.factories import make_shopping_list
from foodgram import models
from users.models import Subscription

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    http_method_names: tuple = (
        HttpMethod.GET,
        HttpMethod.POST,
        HttpMethod.PUT,
        HttpMethod.DELETE,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    )
    lookup_value_regex = LOOKUP_DIGIT_PATTERN
    queryset = User.objects.all()

    @action((HttpMethod.GET,), detail=False,
            permission_classes=(IsAuthenticated,))
    def me(self, request: Request) -> Response:
        return Response(
            self.get_serializer(request.user).data, status=status.HTTP_200_OK
        )

    @action((HttpMethod.PUT,), url_path='me/avatar',
            detail=False, serializer_class=UserAvatarSerializer,
            permission_classes=(IsAuthenticated,))
    def avatar(self, request: Request) -> Response:
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request: Request) -> Response:
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=(HttpMethod.GET,), detail=False,
            serializer_class=SubscriptionSerializer,
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request: Request) -> Response:
        authors_qs = User.objects.filter(
            subscriptions_on_author__user=request.user
        ).annotate(recipes_count=Count('recipes')).all()
        serializer = self.get_serializer(self.paginate_queryset(authors_qs),
                                         many=True)
        return self.get_paginated_response(serializer.data)

    @action((HttpMethod.POST,), detail=True,
            serializer_class=SubscribeSerializer,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request: Request, id: str) -> Response:
        serializer = self.get_serializer(data={'author': id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request: Request, id: str) -> Response:
        get_object_or_404(User, pk=id)
        n_removed, _ = Subscription.objects.filter(user=request.user,
                                                   author_id=id).delete()
        return Response(
            data=None if n_removed else {'detail': 'Подписка отсутствует.'},
            status=(status.HTTP_204_NO_CONTENT if n_removed
                    else status.HTTP_400_BAD_REQUEST)
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names: tuple = (
        HttpMethod.GET,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    )
    queryset = models.Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientListFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    http_method_names: tuple = (
        HttpMethod.GET,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    )
    queryset = models.Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names: tuple = (
        HttpMethod.GET,
        HttpMethod.POST,
        HttpMethod.PATCH,
        HttpMethod.DELETE,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS
    )
    lookup_url_kwarg = 'recipe_id'
    lookup_value_regex = LOOKUP_DIGIT_PATTERN
    queryset = models.Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'tags'
    ).annotate(
        is_favorited=Value(False),
        is_in_shopping_cart=Value(False)
    )
    serializer_class = RecipeReadSerializer
    filterset_class = RecipeListFilter
    permission_classes = [IsAuthenticatedOrReadOnly,
                          IsAuthorAdminOrReadOnly]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.auth:
            return queryset

        return queryset.annotate(
            is_favorited=Exists(
                models.Favorite.objects.filter(
                    recipe=OuterRef('pk'), user=self.request.user
                )
            ),
            is_in_shopping_cart=Exists(
                models.ShoppingCart.objects.filter(
                    recipe=OuterRef('pk'), user=self.request.user
                )
            )
        )

    @action((HttpMethod.GET,), detail=True,
            serializer_class=ShortLinkSerializer, url_path='get-link')
    def get_link(self, request: Request, recipe_id: str) -> Response:
        serializer = self.get_serializer(data={'recipe': recipe_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action((HttpMethod.POST,), detail=True,
            serializer_class=FavoriteSerializer,
            permission_classes=(IsAuthenticatedOrReadOnly,))
    def favorite(self, request: Request, recipe_id: str) -> Response:
        return self._add_fav_shop(request, recipe_id)

    @favorite.mapping.delete
    def delete_favorite(self, request: Request, recipe_id: str) -> Response:
        return self._delete_fav_shop(request, recipe_id, models.Favorite)

    @action((HttpMethod.POST,), detail=True,
            serializer_class=ShoppingCartSerializer,
            permission_classes=(IsAuthenticatedOrReadOnly,))
    def shopping_cart(self, request: Request, recipe_id: str) -> Response:
        return self._add_fav_shop(request, recipe_id)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request: Request,
                             recipe_id: str) -> Response:
        return self._delete_fav_shop(request, recipe_id, models.ShoppingCart)

    def _add_fav_shop(self, request: Request, recipe_id: str) -> Response:
        serializer = self.get_serializer(data={'recipe': recipe_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_fav_shop(self, request: Request,
                         recipe_id: str, model: Type[Model]) -> Response:
        get_object_or_404(models.Recipe, pk=recipe_id)
        n_removed, _ = model.objects.filter(
            user=request.user, recipe_id=recipe_id
        ).delete()

        return Response(
            data=None if n_removed else {
                'detail': ('Рецепт не был добавлен в '
                           f'`{model._meta.verbose_name.title()}`.')
            },
            status=(status.HTTP_204_NO_CONTENT if n_removed
                    else status.HTTP_400_BAD_REQUEST)
        )

    @action((HttpMethod.GET,), detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request: Request) -> HttpResponseBase:
        ingredients = models.RecipeIngredient.objects.select_related(
            'ingredient'
        ).filter(
            recipe__shoppingcart__user_id=request.user.id
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount')).order_by('name')

        return FileResponse(make_shopping_list(ingredients),
                            as_attachment=True,
                            filename='shopping-cart.txt',
                            content_type='text/plain')
