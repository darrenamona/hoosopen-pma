import json
import os
from django.core.management.base import BaseCommand
from hoosopen.models import Tag

class Command(BaseCommand):

    help = 'Load tags from initial.json'
    
    def handle(self, *args, **kwargs):
        with open(os.path.join(os.path.dirname(__file__), '..', '..', 'initial.json'), 'r') as file:
            data = json.load(file)
            for entry in data:
                if entry['model'] == 'myapp.tag':
                    tag_name = entry['fields']['name']
                    Tag.objects.get_or_create(name=tag_name)
        self.stdout.write(self.style.SUCCESS('Successfully loaded tags.'))