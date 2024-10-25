from secrets import token_urlsafe
from typing import Type

from django.contrib.auth import get_user_model
from django.db.models import Model, Sum
from django.db.models.functions import Lower
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
from rest_framework.serializers import ModelSerializer

from api.const import (LOOKUP_DIGIT_PATTERN, SHORT_LINK_TOKEN_NBYTES,
                       SHORT_LINK_URL_PATH, HttpMethod)
from api.filters import IngredientListFilter, RecipeListFilter
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (AvatarSerializer, FavoriteShoppingCartSerializer,
                             IngredientSerializer, RecipeCreateSerializer,
                             RecipeReadSerializer, RecipeUpdateSerializer,
                             SubscriptionSerializer, TagSerializer)
from foodgram import models

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
    serializer_class = RecipeReadSerializer
    filterset_class = RecipeListFilter
    permission_classes = [IsAuthenticatedOrReadOnly,
                          IsAuthorAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        elif self.action == 'partial_update':
            return RecipeUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer: ModelSerializer) -> None:
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        kwargs.pop('partial')
        return super().update(request, *args, **kwargs)

    def _get_recipe(self, recipe_id: str):
        return get_object_or_404(models.Recipe.objects, pk=recipe_id)

    def _make_token(self, nbytes: int) -> str:
        while True:
            token = token_urlsafe(nbytes)
            if not models.RecipeShortLink.objects.filter(token=token).exists():
                break
        return token

    @action([HttpMethod.GET], detail=True, url_path='get-link')
    def get_link(self, request: Request, recipe_id: str) -> Response:
        recipe = self._get_recipe(recipe_id)
        try:
            token = recipe.link_token.token
        except models.RecipeShortLink.DoesNotExist:
            token = self._make_token(SHORT_LINK_TOKEN_NBYTES)
            models.RecipeShortLink.objects.create(recipe=recipe, token=token)

        return Response(
            {'short-link': request.build_absolute_uri(
                f'/{SHORT_LINK_URL_PATH}{token}'
            )}
        )

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

    def add_to_fav_or_shop_cart(self, request: Request, recipe_id: str,
                                inter_model: Type[Model]) -> Response:
        recipe = self._get_recipe(recipe_id)
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

    @action([HttpMethod.GET], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request: Request) -> HttpResponseBase:
        recipes_id = tuple(
            item['recipe_id'] for item
            in request.user.shopping_cart.all().values('recipe_id')
        )
        if not recipes_id:
            ValidationError({self.action: 'Корзина пуста.'})

        ingredients = models.RecipeIngredient.objects.filter(
            recipe_id__in=recipes_id
        ).select_related('ingredient').values(
            name=Lower('ingredient__name'),
            unit=Lower('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount'))

        to_response = '\n'.join(((f'{item["name"]} — '
                                  f'{item["amount"]} {item["unit"]}')
                                 for item in ingredients))
        return FileResponse(to_response, as_attachment=True,
                            filename='shopping-cart.txt',
                            content_type='text/plain')
