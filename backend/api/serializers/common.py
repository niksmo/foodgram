from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from foodgram.models import Recipe


class CommonRecipeReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CommonFavoriteShopCartSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('recipe',)
        extra_kwargs = {
            'recipe': {'write_only': True}
        }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if self.Meta.model.objects.filter(
            user=self.context['request'].user,
            recipe=attrs['recipe']
        ).exists():
            raise ValidationError('Рецепт уже добавлен.')

        return attrs

    def create(self, validated_data):
        return self.Meta.model.objects.create(
            user=self.context['request'].user,
            recipe=validated_data['recipe']
        )

    def to_representation(self, instance):
        return CommonRecipeReadSerializer(instance.recipe,
                                          context=self.context).data
