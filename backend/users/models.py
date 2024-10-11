from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy


class MyUser(AbstractUser):
    email = models.EmailField(gettext_lazy('email address'), unique=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_admin(self) -> bool:
        return self.is_staff
