from dataclasses import dataclass

LOOKUP_DIGIT_PATTERN = r'\d+'
SHORT_LINK_TOKEN_NBYTES = 4
SHORT_LINK_URL_PATH = 's/'
SMALL_INTEGER_FIELD_MAX_VALUE = 32767


@dataclass(frozen=True)
class HttpMethod:
    GET = 'get'
    POST = 'post'
    DELETE = 'delete'
    PUT = 'put'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'
