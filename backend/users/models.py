from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy


class MyUser(AbstractUser):
    email = models.EmailField(gettext_lazy('email address'), unique=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True)

    follow = models.ManyToManyField('self',
                                    symmetrical=False,
                                    through='Subscription',
                                    through_fields=('user', 'author'),
                                    related_name='+')

    followers = models.ManyToManyField('self',
                                       symmetrical=False,
                                       through='Subscription',
                                       through_fields=('author', 'user'),
                                       related_name='+')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_admin(self) -> bool:
        return self.is_staff


class Subscription(models.Model):
    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='+')
    author = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='+')

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user__exact=models.F('author')),
                name='user_cant_follow_on_self')
        ]
