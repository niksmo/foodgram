from dataclasses import dataclass

LOOKUP_DIGIT_PATTERN = r'\d+'


@dataclass(frozen=True)
class HttpMethod:
    GET = 'get'
    POST = 'post'
    DELETE = 'delete'
    PUT = 'put'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'
