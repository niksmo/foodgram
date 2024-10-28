from django.contrib.auth.models import AbstractUser
from django.db import models

from core.const import MAX_EMAIL_LENGTH, MAX_USER_FIRST_LAST_NAME_LENGTH
from core.factories import make_model_str


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS: tuple[str, ...] = ('username', 'first_name', 'last_name')

    first_name = models.CharField('Имя',
                                  max_length=MAX_USER_FIRST_LAST_NAME_LENGTH)

    last_name = models.CharField('Фамилия',
                                 max_length=MAX_USER_FIRST_LAST_NAME_LENGTH)

    email = models.EmailField('Электронная почта', unique=True,
                              max_length=MAX_EMAIL_LENGTH)

    avatar = models.ImageField('Аватар', upload_to='avatars', blank=True)

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return make_model_str(self.username)


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='пользователь'
    )

    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions_on_author',
        verbose_name='автор'
    )

    class Meta:
        ordering = ('author__username',)
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscriptions'
            ),
            models.CheckConstraint(
                check=~models.Q(user__exact=models.F('author')),
                name='user_cant_follow_on_self')
        )

    def __str__(self) -> str:
        return make_model_str(f'Запись в подписках <id: {self.pk}>')
