from django.views import View
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404

from .models import RecipeShortLink
from .const import FRONTEND_RECIPES_PATH


class RecipeShortLinkView(View):
    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        breakpoint()
        short_link = get_object_or_404(
            RecipeShortLink.objects.select_related('recipe'),
            token=token
        )
        return HttpResponsePermanentRedirect(
            request.build_absolute_uri(
                f'/{FRONTEND_RECIPES_PATH}{short_link.recipe.pk}/'
            )
        )
