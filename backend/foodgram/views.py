from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.views import View

from foodgram.const import FRONTEND_RECIPES_PATH
from foodgram.models import RecipeShortLink


class RecipeShortLinkView(View):
    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        short_link = get_object_or_404(
            RecipeShortLink.objects.select_related('recipe'),
            token=token
        )
        return HttpResponsePermanentRedirect(
            request.build_absolute_uri(
                f'/{FRONTEND_RECIPES_PATH}{short_link.recipe.pk}/'
            )
        )
