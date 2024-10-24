from django.urls import path

from api.const import SHORT_LINK_URL_PATH

from .views import RecipeShortLinkView


urlpatterns = [
    path(f'{SHORT_LINK_URL_PATH}<slug:token>', RecipeShortLinkView.as_view())
]
