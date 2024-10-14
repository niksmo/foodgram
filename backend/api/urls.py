from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='users')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('tags', views.TagViewSet, basename='tags')

urlpatterns = router.urls
