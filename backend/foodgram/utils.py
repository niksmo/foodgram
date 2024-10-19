from .const import (DEFAULT_MODEL_ADMIN_NAME_LENGTH,
                    DEFAULT_MODEL_ADMIN_NAME_SUFFIX)


def get_model_admin_name(field: str,
                         max_length: int = DEFAULT_MODEL_ADMIN_NAME_LENGTH,
                         suffix: str = DEFAULT_MODEL_ADMIN_NAME_SUFFIX):
    assert isinstance(field, str) and len(field) > 0, (
        '`field` length should more then `0`'
    )
    assert max_length > 0, (
        '`max_length` should be more then `0`'
    )
    assert len(suffix) < max_length, (
        '`suffix` length should be `<= max length`'
    )

    if len(field) - max_length <= 0:
        return field

    return (f'{field[:max_length - len(suffix)] }'
            f'{suffix}')
