from secrets import token_urlsafe
from typing import Type

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Model, Sum
from django.http.response import FileResponse, HttpResponseBase
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ModelSerializer

from api.filters import IngredientListFilter, RecipeListFilter
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeReadSerializer,
                             RecipeUpdateSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserAvatarSerializer)
from core.const import (LOOKUP_DIGIT_PATTERN, SHORT_LINK_SLUG_NBYTES,
                        SHORT_LINK_URL_PATH, HttpMethod)
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

    @action([HttpMethod.GET], detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request: Request) -> Response:
        self.get_object = self.get_instance
        return self.retrieve(request)

    @action([HttpMethod.PUT], url_path='me/avatar',
            detail=False, serializer_class=UserAvatarSerializer,
            permission_classes=[IsAuthenticated])
    def avatar(self, request: Request) -> Response:
        self.get_object = self.get_instance
        return self.update(request)

    @avatar.mapping.delete
    def delete_avatar(self, request: Request) -> Response:
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=[HttpMethod.GET], detail=False,
            serializer_class=SubscriptionSerializer,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request: Request) -> Response:
        authors = User.objects.filter(
            subscriptions_on_author__user=request.user
        ).annotate(recipes_count=Count('recipes')).all()
        serializer = self.get_serializer(self.paginate_queryset(authors),
                                         many=True)
        return self.get_paginated_response(serializer.data)

    @action([HttpMethod.POST], detail=True,
            serializer_class=SubscriptionSerializer,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request: Request, id: str) -> Response:
        author = get_object_or_404(
            User.objects.annotate(recipes_count=Count('recipes')),
            pk=id
        )
        serializer = self.get_serializer(data={'author_id': author.pk,
                                               'user_id': request.user.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request: Request, id: str) -> Response:
        get_object_or_404(User, pk=id)
        n_removed, _ = Subscription.objects.filter(
            user=request.user, author_id=id
        ).delete()

        if not n_removed:
            raise ValidationError({self.action: 'Подписка отсутствует.'})

        return Response(status=status.HTTP_204_NO_CONTENT)


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
    ).prefetch_related('tags')
    serializer_class = RecipeReadSerializer
    filterset_class = RecipeListFilter
    permission_classes = [IsAuthenticatedOrReadOnly,
                          IsAuthorAdminOrReadOnly]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == 'create':
            return RecipeCreateSerializer
        elif self.action == 'partial_update':
            return RecipeUpdateSerializer
        elif self.action == 'favorite':
            return FavoriteSerializer
        elif self.action == 'shopping_cart':
            return ShoppingCartSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer: ModelSerializer) -> None:
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        kwargs.pop('partial')
        return super().update(request, *args, **kwargs)

    def _make_short_link_slug(self, nbytes: int) -> str:
        while True:
            token = token_urlsafe(nbytes)
            if not models.RecipeShortLink.objects.filter(token=token).exists():
                break
        return token

    @action([HttpMethod.GET], detail=True, url_path='get-link')
    def get_link(self, request: Request, recipe_id: str) -> Response:
        recipe = get_object_or_404(models.Recipe.objects, pk=recipe_id)
        try:
            slug = recipe.link_slug.slug
        except models.RecipeShortLink.DoesNotExist:
            slug = self._make_short_link_slug(SHORT_LINK_SLUG_NBYTES)
            models.RecipeShortLink.objects.create(recipe=recipe, slug=slug)

        return Response(
            {'short-link': request.build_absolute_uri(
                f'/{SHORT_LINK_URL_PATH}{slug}'
            )}
        )

    @action([HttpMethod.POST], detail=True,
            serializer_class=FavoriteSerializer,
            permission_classes=[IsAuthenticatedOrReadOnly])
    def favorite(self, request: Request, recipe_id: str) -> Response:
        return self._add_fav_shop(request, recipe_id)

    @favorite.mapping.delete
    def delete_favorite(self, request: Request, recipe_id: str) -> Response:
        return self._delete_fav_shop(request, recipe_id, models.Favorite)

    @action([HttpMethod.POST], detail=True,
            serializer_class=ShoppingCartSerializer,
            permission_classes=[IsAuthenticatedOrReadOnly])
    def shopping_cart(self, request: Request, recipe_id: str) -> Response:
        return self._add_fav_shop(request, recipe_id)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request: Request,
                             recipe_id: str) -> Response:
        return self._delete_fav_shop(request, recipe_id, models.ShoppingCart)

    def _add_fav_shop(self, request: Request, recipe_id: str) -> Response:
        serializer = self.get_serializer(data={'user_id': request.user.id,
                                               'recipe_id': recipe_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_fav_shop(self, request: Request,
                         recipe_id: str, model: Type[Model]) -> Response:
        get_object_or_404(models.Recipe, pk=recipe_id)
        n_removed, _ = model.objects.filter(
            user=request.user, recipe_id=recipe_id
        ).delete()

        if not n_removed:
            raise ValidationError({self.action: 'Рецепт не был добавлен.'})

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action([HttpMethod.GET], detail=False,
            permission_classes=[IsAuthenticated])
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
