from django.contrib import admin as admin_site
from django.contrib.auth import admin, get_user_model, models

from users.models import Subscription


@admin_site.register(get_user_model())
class UserAdmin(admin.UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'avatar',
        'last_login',
        'date_joined'
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


@admin_site.register(Subscription)
class SubscriptionAdmin(admin_site.ModelAdmin):
    list_display = ('user', 'author')
    list_display_links = ('user',)


admin_site.site.unregister(models.Group)
