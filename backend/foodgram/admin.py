from django.contrib import admin
from django.db.models import Count
from django.db.models.query import QuerySet
from django.http import HttpRequest

from foodgram.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                             RecipeShortLink, ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_select_related = ('author',)
    list_display = ('name', 'author', 'created_at',
                    'tags_list', 'ingredients_list', 'n_favorites')
    readonly_fields = ('n_favorites',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = (RecipeIngredientInLine,)

    fieldsets = (
        (None,
            {'fields': ('name', 'text', 'image',
                        'cooking_time', 'author', 'tags')}),

        ('Статистика',
         {'fields': ('n_favorites',)}),
    )

    def _make_list_str(self, obj: Recipe, attr: str) -> str:
        return ', '.join((item.name for item in getattr(obj, attr).all()))

    @admin.display(description='в избранное')
    def n_favorites(self, obj: Recipe) -> int:
        return obj.favorite__count

    @admin.display(description='теги')
    def tags_list(self, obj: Recipe) -> str:
        return self._make_list_str(obj, 'tags')

    @admin.display(description='ингредиенты')
    def ingredients_list(self, obj: Recipe) -> str:
        return self._make_list_str(obj, 'ingredients')

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).prefetch_related(
            'tags', 'ingredients'
        ).annotate(Count('favorite')).order_by('-created_at')


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')
    list_display_links = ('recipe',)


@admin.register(ShoppingCart)
class ShoppingCartRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')
    list_display_links = ('recipe',)


@admin.register(RecipeShortLink)
class RecipeShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'slug')
    list_display_links = ('recipe',)
