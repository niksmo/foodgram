from api.serializers.common import CommonFavoriteShopCartSerializer
from foodgram.models import ShoppingCart


class ShoppingCartSerializer(CommonFavoriteShopCartSerializer):
    class Meta(CommonFavoriteShopCartSerializer.Meta):
        model = ShoppingCart
