![workflow badge](https://github.com/niksmo/foodgram/actions/workflows/main.yml/badge.svg)

# Проект Foodgram

Задеплоен и доступен по URL https://foodgram.nks-tech.ru

## Функции:

- Авторизация
- Просмотр рецептов созданных пользователями
- Добавление рецепта
- Редактирование рецепта
- Добавление рецепта в избранное
- Удаление рецепта из избранного
- Добавление рецепта в список покупок
- Удаление рецепта из списка покупок
- Скачивание списка покупок в формате .txt
- Подписаться на автора рецепта
- Отписаться от автора рецепта

## Стэк

Бэкенд:

- Python 3.9
- Django REST framework 3.15


Фронтенд:

- React 16.6
- ReactRouter 5.2

## Как запустить проект локально

Требуется установленный Docker [инстукция по установке](https://docs.docker.com/get-started/get-docker/)

1. Скопировать файлы в локальную директорию:
- `.env.example`
- `compose.production.yml`

2. Переименовать `.env.example` в `.env`
3. Переименовать `compose.production.yml` в `compose.yml`
4. Изменить значения переменных в `.env` (см. ниже)
5. Запустить контейнеры с помощью `Docker` в фоновом режиме:

```sh
cd <your_local_dir_with_.env_and_docker-compose.yml>
docker compose up -d
```

##  Значения ENV переменных

DJANGO_DEBUG - состояние дебаг-режима для Django, например `True` - проект будет запущен на локальной СУБД SQLite.

DJANGO_SECRET_KEY - значение секретного ключа Django, рекомендуется использовать 256 битную случайную последовательность

DJANGO_ALLOWED_HOSTS - список разрешённых хостов для Django, список указывается в `'` или `"` через пробел, например:

```"127.0.0.1 host1 host2"```

DJANGO_CSRF_TRUSTED_ORIGINS - должен быть хост с указанием схемы, например `https://mysite.com`

POSTGRES_USER - имя пользователя базы данных

POSTGRES_PASSWORD - пароль к базе данных

POSTGRES_DB - название базы данных

POSTGRES_HOST - доменное имя контейнера с базой данных, должно быть `db`

POSTGRES_PORT - порт контейнера с базой данных, должен быть `5432`

GATEWAY_HOST - ip-адрес веб-сервера

GATEWAY_PORT - порт веб-сервера

## Авторы

[niksmo](https://github.com/niksmo)
