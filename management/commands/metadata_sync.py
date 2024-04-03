import sys
from datetime import datetime

from django.core.management.base import BaseCommand

from lon import settings
from metadata.models import LONMetadataSync
from metadata.utils import MetadataSync, GitRepo, ObjectStore

BUCKET_NAME = "LightsOn-Metadata-bucket"
BUCKET_FOLDER_LOCATION = f"lon-{settings.DEPLOYMENT_MODE}"
DATA_DIR = 'metadata/local_data'


class Command(BaseCommand, MetadataSync, GitRepo, ObjectStore):
    help = """
        This management command exports site metadata to JSON files and imports data from JSON files to the database.

        Usage:
             metadata_sync [(--import | --export)] [--push (github | bucket | all | none)]
    
        Options:
            -e, --export   Exports metadata from the database to JSON files.
            -i, --import   Imports data from JSON files to the database.
                       (either --export or --import is required)
    
            -p, --push     (optional) Specifies where the exported JSON files are pushed. 
                            If not specified defaults to 'all'
                            
                            github: Pushes exported data to GitHub repository.
                            bucket: Pushes exported data to Object Store.
                            all: Pushes data to both GitHub and Object Store.
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
        start_time = datetime.now()
        super().__init__()
        self.local_data_dir = DATA_DIR
        git_repo = GitRepo()
        bucket = ObjectStore(BUCKET_NAME, DATA_DIR)
        all_models = LONMetadataSync.objects.filter(is_active=True)
        meta_tree = self.get_meta_tree(all_models)
        dependency_map = {
            model_name: set(model_data["dependency"])
            for model_name, model_data in meta_tree.items()
        }
        models_to_process = self.topological_sort(dependency_map, all_models)
        model_qs_mapper = {}
        files_to_upload = []
        count, total = 0, len(models_to_process)
        git_repo.git_checkout()
        for model in models_to_process:
            count += 1
            current_model_app = f'{model.app_name}.{model.model_name}'
            sys.stdout.write(f'({count}/{total}) {current_model_app}...')
            if options['export']:
                self.export_json(model, current_model_app, meta_tree[current_model_app],
                                 model_qs_mapper)
                files_to_upload.append(f'{model.report_name}/{current_model_app}.json')

            self.stdout.write('Done')

        if options['push'] in ('all', 'bucket') and options['export']:
            self.stdout.write('Pushing to Object Store...')
            for file in files_to_upload:
                bucket.upload_files_to_object_storage(
                    file, BUCKET_FOLDER_LOCATION
                )
        if options['push'] in ('all', 'github') and options['export']:
            self.stdout.write('Pushing to Git...')
            git_repo.git_commit(files_to_upload)

        self.stdout.write(self.style.SUCCESS(
            f"Data {'exported' if options['export'] else 'imported'} successfully!"))

        self.stdout.write(f'Completed in {(datetime.now() - start_time).total_seconds()} seconds')
