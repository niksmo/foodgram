from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy


class MyUser(AbstractUser):
    email = models.EmailField(gettext_lazy('email address'), unique=True)
    avatar = models.ImageField('Аватар', upload_to='avatars', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self) -> str:
        return self.username

    @property
    def is_admin(self) -> bool:
        return self.is_staff


class Subscription(models.Model):
    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE,
        related_name='subscriptions_set',
        verbose_name='пользователь'
    )

    author = models.ForeignKey(
        MyUser, on_delete=models.CASCADE,
        related_name='subscribers_set',
        verbose_name='автор'
    )

    class Meta:
        ordering = ('author__username',)
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscriptions'
            ),
            models.CheckConstraint(
                check=~models.Q(user__exact=models.F('author')),
                name='user_cant_follow_on_self')
        ]

    def __str__(self) -> str:
        return f'Запись в подписках <id: {self.pk}>'
