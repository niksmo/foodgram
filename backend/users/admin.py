from django.contrib import admin as admin_site
from django.contrib.auth import admin, get_user_model, models


@admin_site.register(get_user_model())
class UserAdmin(admin.UserAdmin):
    pass


admin_site.site.unregister(models.Group)
