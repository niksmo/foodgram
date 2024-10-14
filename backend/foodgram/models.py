from django.contrib.auth import get_user_model
from django.db import models


class Ingredient(models.Model):
    name = models.CharField('Название',
                            max_length=128,
                            unique=True,
                            blank=False)

    measurement_unit = models.CharField('Единица измерения',
                                        max_length=64,
                                        blank=False)

    class Meta:
        pass


class Tag(models.Model):
    name = models.CharField('Название',
                            max_length=32,
                            unique=True,
                            blank=False)

    slug = models.SlugField(max_length=32,
                            unique=True,
                            blank=False)

    class Meta:
        pass
