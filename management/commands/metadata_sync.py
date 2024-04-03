from datetime import datetime

from django.core.management.base import BaseCommand

from metadata.utils import ExportMetadata


class Command(BaseCommand):
    help = 'Exports data to JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '-p', '--push',
            choices=['github', 'bucket', 'none', 'all'],
            default='all',
            required=False,
            help='Push to perform: github, bucket, none or all'
        )
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '-e', '--export',
            action='store_true',
            help='Flag to indicate exporting data'
        )
        group.add_argument(
            '-i', '--import',
            action='store_true',
            help='Flag to indicate importing data'
        )

    def handle(self, *args, **options):
        push_option = options['push']
        start_time = datetime.now()
        if options['export']:
            ExportMetadata().process(push_option)
            self.stdout.write(self.style.SUCCESS("Data exported successfully!"))

        self.stdout.write(f'Completed in {(datetime.now() - start_time).total_seconds()} seconds')
