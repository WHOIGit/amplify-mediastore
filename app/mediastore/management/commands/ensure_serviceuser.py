import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Creates a user non-interactively if it doesn't exist"

    def add_arguments(self, parser):
        parser.add_argument('--username', help="Username")
        parser.add_argument('--password', help="User password")

    def handle(self, *args, **options):
        User = get_user_model()
        if all([options[k] is None for k in 'username password'.split()]):
            options['username'] = os.environ.get('DJANGO_SERVICEUSER_USERNAME')
            options['password'] = os.environ.get('DJANGO_SERVICEUSER_PASSWORD')

        if options['username'] and options['password'] and \
           not User.objects.filter(username=options['username']).exists():
            User.objects.create_user(username=options['username'],
                                     password=options['password'])
