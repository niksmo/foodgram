from collections.abc import Collection, Iterable
from typing import Any

from rest_framework.exceptions import ValidationError

from foodgram.models import Ingredient


def empty_image_validator(value) -> None:
    if not value:
        raise ValidationError('Это поле не может быть пустым.')


class RecipeCreateUpdateValidator:
    """
    A class for verifying:
    - repetition ids in tags, ingredients fields

    - existing ingredients
    """

    def __init__(self) -> None:
        self._ingredients_field = 'ingredients'
        self._tags_field = 'tags'
        self._fields_verbose = {
            self._tags_field: 'Теги',
            self._ingredients_field: 'Ингредиенты'
        }
        self._repetition_message = '{field} с ID {ids} дублируются.'

    def __call__(self, values: dict[str, Any]) -> None:
        errors = {}

        self._verify_repetition(self._tags_field,
                                (tag.pk for tag in values[self._tags_field]),
                                errors)

        ing_unique_ids = self._verify_repetition(
            self._ingredients_field,
            (item['ingredient_id']
             for item in values['recipe_ingredient']),
            errors
        )

        # tags exists verified by PrimaryKeyRelatedField
        self._verify_ingredients_exists(ing_unique_ids, errors)

        if errors:
            raise ValidationError(errors)

    def _verify_repetition(
        self, field_name: str,
            ids: Iterable[int],
            errors: dict[str, Any]
    ) -> list[int]:
        doubles_set: set[int] = set()
        unique_set: set[int] = set()
        for id in ids:
            if id in unique_set:
                doubles_set.add(id)
            else:
                unique_set.add(id)

        if doubles_set:
            errors[field_name] = [
                {
                    'id': [
                        self._repetition_message.format(
                            field=self._fields_verbose[field_name],
                            ids=sorted(doubles_set)
                        )]
                }
            ]
        return sorted(unique_set)

    def _verify_ingredients_exists(self,
                                   ids: Collection[int],
                                   errors: dict[str, Any]) -> None:
        exists_list = Ingredient.objects.filter(pk__in=ids).all()

        if len(exists_list) == len(ids):
            return

        exists_pk_set = {instance.pk for instance in exists_list}
        not_exists = [pk
                      for pk in ids
                      if pk not in exists_pk_set]

        exists_message = (f'{self._fields_verbose[self._ingredients_field]} '
                          f'с ID {not_exists} '
                          'не существуют.')

        if self._ingredients_field in errors:
            errors[self._ingredients_field].append({'id': [exists_message]})
        else:
            errors[self._ingredients_field] = [
                {'id': [exists_message]}
            ]
