from rest_framework import serializers

from foodgram import models


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
