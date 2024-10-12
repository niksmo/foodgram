import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from foodgram.models import Ingredient


class Command(BaseCommand):
    help = ('Load ingredients data from path '
            '<project_root>/data/ingredients.json')

    path = settings.BASE_DIR.parent / 'data/ingredients.json'

    def add_arguments(self, parser):
        parser.add_argument('--file', help='Custom file path', type=str)

    def handle(self, *args, **kwargs):
        if kwargs['file']:
            self.path = Path(kwargs['file']).resolve()

        if not self.path.exists():
            raise CommandError(f'File not exists, path: {self.path}')

        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError as exc:
            raise CommandError(f'Json is broken: {exc!r}')

        for item in data:
            try:
                Ingredient.objects.create(**item)
            except Exception as exc:
                self.stdout.write(self.style.NOTICE(f'{exc!r}'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Insert ingredient: {item}')
                )
