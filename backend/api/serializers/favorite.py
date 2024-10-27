from api.serializers.common import CommonFavoriteShopCartSerializer
from foodgram.models import Favorite


class FavoriteSerializer(CommonFavoriteShopCartSerializer):
    class Meta(CommonFavoriteShopCartSerializer.Meta):
        model = Favorite
