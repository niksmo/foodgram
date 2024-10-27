from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponsePermanentRedirect
from django.views import View

from core.const import FRONTEND_RECIPES_PATH
from foodgram.models import RecipeShortLink


class RecipeShortLinkView(View):
    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        try:
            short_link = RecipeShortLink.objects.select_related(
                'recipe').get(token=token)
        except RecipeShortLink.DoesNotExist:
            redirect_url = request.build_absolute_uri('/not_found')
        else:
            redirect_url = request.build_absolute_uri(
                f'/{FRONTEND_RECIPES_PATH}{short_link.recipe.pk}/'
            )

        return HttpResponsePermanentRedirect(redirect_url)
