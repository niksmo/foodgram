from typing import Any

from rest_framework.exceptions import ValidationError


def repetitions_id_validator(values: list[Any]) -> None:
    if isinstance(values[0], dict):
        values = [item['id'] for item in values]

    doubles_set = set()
    unique_set = set()
    for pk in values:
        if pk in unique_set:
            doubles_set.add(pk)
        else:
            unique_set.add(pk)

    if doubles_set:
        raise ValidationError(f'Дублируются ID {sorted(doubles_set)}')


def empty_image_validator(value) -> None:
    if not value:
        raise ValidationError('Это поле не может быть пустым.')
