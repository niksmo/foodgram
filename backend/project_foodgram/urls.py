from django.contrib import admin
from django.urls import include, path

from core.const import SHORT_LINK_URL_PATH
from foodgram.views import RecipeShortLinkView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(f'{SHORT_LINK_URL_PATH}<slug:token>', RecipeShortLinkView.as_view())
]
