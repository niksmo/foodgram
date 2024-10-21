from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.db.models import Count

from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class RecipeTagInLine(admin.TabularInline):
    model = RecipeTag


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient


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
