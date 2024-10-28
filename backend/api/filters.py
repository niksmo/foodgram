import django_filters

from foodgram.models import Ingredient, Recipe, Tag


class IngredientListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeListFilter(django_filters.FilterSet):
    tags = django_filters.filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False,
    )
    is_favorited = django_filters.rest_framework.BooleanFilter(
        method='get_favorite'
    )

    is_in_shopping_cart = django_filters.rest_framework.BooleanFilter(
        method='get_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def get_favorite(self, queryset, name, value):
        if int(value):
            queryset = queryset.filter(favorite__user=self.request.user)
        return queryset

    def get_shopping_cart(self, queryset, name, value):
        if int(value):
            queryset = queryset.filter(shoppingcart__user=self.request.user)
        return queryset
