import django_filters

from foodgram.models import Ingredient, Recipe, Tag

BOOL_CHOICES = (
    (0, False),
    (1, True),
)


class IngredientListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeListFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(field_name='author__id')
    tags = django_filters.filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False,
    )
    is_favorited = django_filters.TypedChoiceFilter(
        choices=BOOL_CHOICES,
        method='get_favorite'
    )

    is_in_shopping_cart = django_filters.TypedChoiceFilter(
        choices=BOOL_CHOICES,
        method='get_shopping_cart'
    )

    def get_favorite(self, queryset, name, value):
        if self.request.auth and int(value):
            queryset = queryset.filter(
                pk__in=(item.recipe.id for item
                        in self.request.user.favorite_set.all())
            )
        return queryset

    def get_shopping_cart(self, queryset, name, value):
        if self.request.auth and int(value):
            queryset = queryset.filter(
                pk__in=(item.recipe.id for item
                        in self.request.user.shoppingcart_set.all())
            )
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags')
