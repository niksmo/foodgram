from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', blank=True)

    @property
    def is_admin(self) -> bool:
        return self.is_staff
