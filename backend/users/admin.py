from django.contrib import admin as admin_site
from django.contrib.auth import admin, get_user_model, models
from django.db.models import Count
from django.db.models.query import QuerySet
from django.http import HttpRequest

from users.models import Subscription, User


@admin_site.register(get_user_model())
class UserAdmin(admin.UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'avatar',
        'date_joined',
        'n_users_recipes',
        'n_subscribers'
    )

    fieldsets = (
        (None,
         {'fields': ('username', 'password')}),

        ('Персональная информация',
         {'fields': ('first_name', 'last_name', 'email', 'avatar')}),

        ('Права доступа',
         {'fields': ('is_active', 'is_staff', 'is_superuser',)}),

        (None,
         {'fields': ('last_login', 'date_joined')}),
    )

    list_filter = ('is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)

    @admin_site.display(description='подписчиков')
    def n_subscribers(self, obj: User) -> int:
        return obj.subscriptions_on_author__count

    @admin_site.display(description='рецептов')
    def n_users_recipes(self, obj: User) -> int:
        return obj.recipes__count

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).annotate(
            Count('subscriptions_on_author'), Count('recipes')
        )


@admin_site.register(Subscription)
class SubscriptionAdmin(admin_site.ModelAdmin):
    list_display = ('author', 'user')
    list_display_links = ('author',)
    ordering = ('author__username',)


admin_site.site.unregister(models.Group)
