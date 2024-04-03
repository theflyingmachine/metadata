from datetime import datetime

from django.core.management.base import BaseCommand

from metadata.utils import ExportMetadata


class Command(BaseCommand):
    help = """
        This management command exports site metadata to JSON files and imports data from JSON files to the database.

        Usage:
             metadata_sync [(--import | --export)] [--push (github | bucket | all | none)]
    
        Options:
            -e, --export   Exports metadata from the database to JSON files.
            -i, --import   Imports data from JSON files to the database.
                       (either --export or --import is required)
    
            -p, --push     (optional) Specifies where the exported JSON files are pushed:
                            github: Pushes exported data to GitHub repository.
                            bucket: Pushes exported data to Object Store.
                            all: (default) Pushes data to both GitHub and Object Store.
                            none: Only generates JSON files locally without pushing.
        """

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '-e', '--export', action='store_true', help='Flag to indicate exporting data'
        )
        group.add_argument(
            '-i', '--import', action='store_true', help='Flag to indicate importing data'
        )
        parser.add_argument(
            '-p',
            '--push',
            choices=['github', 'bucket', 'none', 'all'],
            default='all',
            required=False,
            help='Push to perform: github, bucket, none or all',
        )

    def handle(self, *args, **options):
        push_option = options['push']
        start_time = datetime.now()
        if options['export']:
            ExportMetadata().process(push_option)
            self.stdout.write(self.style.SUCCESS("Data exported successfully!"))

        self.stdout.write(f'Completed in {(datetime.now() - start_time).total_seconds()} seconds')
