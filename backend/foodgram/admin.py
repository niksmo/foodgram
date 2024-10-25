from django.contrib import admin
from django.db.models import Count
from django.db.models.query import QuerySet
from django.http import HttpRequest

from foodgram.models import (FavoriteRecipe, Ingredient, Recipe,
                             RecipeIngredient, RecipeShortLink,
                             ShoppingCartRecipe, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class RecipeTagInLine(admin.TabularInline):
    model = Recipe.tags.through
    min_num = 1


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_select_related = ('author',)
    list_display = ('name', 'author', 'created_at', 'n_favorites')
    readonly_fields = ('n_favorites',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = [
        RecipeTagInLine,
        RecipeIngredientInLine
    ]

    fieldsets = (
        (None,
         {'fields': ('name', 'text', 'image', 'cooking_time', 'author')}),

        ('Статистика',
         {'fields': ('n_favorites',)}),
    )

    @admin.display(description='добавлений в избранное')
    def n_favorites(self, obj):
        return obj.in_favorites__count

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).annotate(Count('in_favorites'))


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')
    list_display_links = ('recipe',)


@admin.register(ShoppingCartRecipe)
class ShoppingCartRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')
    list_display_links = ('recipe',)


@admin.register(RecipeShortLink)
class RecipeShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'token')
    list_display_links = ('recipe',)
