from typing import Any

from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from foodgram.models import Recipe


class CommonRecipeReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CommonFavoriteShopCartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        fields = ('recipe', 'user')
        validators = tuple()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        model = self.Meta.model

        if model.objects.filter(
            user=attrs['user'],
            recipe=attrs['recipe']
        ).exists():
            raise ValidationError(
                f'Рецепт уже добавлен в `{model._meta.verbose_name.title()}`.'
            )

        return attrs

    def to_representation(self, instance: Model):
        return CommonRecipeReadSerializer(instance.recipe,
                                          context=self.context).data
