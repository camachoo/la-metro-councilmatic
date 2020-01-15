from itertools import chain

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError

from legistar.bills import LegistarAPIBillScraper
from lametro.models import LAMetroSubject
from opencivicdata.legislative.models import Bill


class Command(BaseCommand):
    def handle(self, *args, **options):

        scraper = LegistarAPIBillScraper()
        scraper.BASE_URL = 'https://webapi.legistar.com/v1/metro'
        scraper.retry_attempts = 0
        scraper.requests_per_minute = 0

        # Topics are removed when a bill is deleted, but there isn't a good
        # mechanism to remove topics that become stale when a bill subject is
        # updated. Remove topics that are not associated with any bills here.
        current_topics = set(chain(*Bill.objects.values_list('subject', flat=True)))
        deleted, _ = LAMetroSubject.objects.exclude(name__in=current_topics).delete()

        self.stdout.write('Removed {0} stale topics'.format(deleted))

        topics = scraper.topics()

        for_update = []

        for topic in topics:
            try:
                subject = LAMetroSubject.objects.get(name=topic['IndexName'])
            except LAMetroSubject.DoesNotExist:
                self.stdout.write('Could not find LAMetroSubject with name {}'.format(topic['IndexName']))
            else:
                subject.guid = topic['api_metadata']
                for_update.append(subject)

        LAMetroSubject.objects.bulk_update(for_update, ['guid'])

        self.stdout.write('Updated {0} topics'.format(len(for_update)))
