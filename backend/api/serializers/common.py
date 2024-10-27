from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from foodgram.models import Recipe


class CommonRecipeReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CommonFavoriteShopCartSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    recipe_id = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        fields = ('user_id', 'recipe_id')

    def validate_recipe_id(self, recipe_id: int) -> int:
        get_object_or_404(Recipe, pk=recipe_id)
        return recipe_id

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if self.Meta.model.objects.filter(
            user_id=attrs['user_id'],
            recipe_id=attrs['recipe_id']
        ).exists():
            raise ValidationError('Рецепт уже добавлен.')

        return attrs

    def create(self, validated_data):
        return self.Meta.model.objects.create(
            user_id=validated_data['user_id'],
            recipe_id=validated_data['recipe_id']
        )

    def to_representation(self, instance):
        return CommonRecipeReadSerializer(instance.recipe,
                                          context=self.context).data
