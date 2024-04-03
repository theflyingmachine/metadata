import ast
import json
from logging import getLogger
from django.apps import apps

from django.core.management import BaseCommand
from datetime import datetime

from django.db import transaction
from django.db.models import ProtectedError

from metadata.management.commands import download_folder_from_object_storage
from metadata.models import LONMetadataSync

logger = getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Import data from json file'
    )

    @staticmethod
    def topological_sort(dependencies):
        visited = set()
        stack = []

        def dfs(node):
            visited.add(node)
            for neighbor in dependencies.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
            stack.append(node)

        for node in dependencies:
            if node not in visited:
                dfs(node)

        return stack

    @staticmethod
    def prepare_filters(filters):
        filter_criteria = {}
        # Split the filter string into key-value pairs
        filter_pairs = filters.split(',')

        # Iterate over each key-value pair and construct the filter criteria
        for pair in filter_pairs:
            key, value = pair.split('=')
            filter_criteria[key.strip()] = value.strip()
        return filter_criteria

    @staticmethod
    def clean_table(ModelClass, export_pref):
        print(f"Cleaning...", end='', flush=True)
        try:
            if export_pref.table_filters:
                filter_criteria = Command.prepare_filters(export_pref.table_filters)
                ModelClass.objects.filter(**filter_criteria).delete()
            else:
                ModelClass.objects.all().delete()
        except ProtectedError:
            raise ValueError

    @staticmethod
    # Function to convert data types based on metadata
    def convert_data_types(json_data, related_obj):
        converted_data = []
        data, metadata, required_by = json_data['data'], json_data['metadata'], json_data['required_by']
        try:
            for item in data:
                for field_name, field_metadata in metadata.items():  # Renamed the loop variable to avoid overwriting
                    if field_metadata['type'] == 'ForeignKey':
                        old_id = field_metadata['field_name']
                        item[field_name] = related_obj[field_metadata['related_model']][item[old_id]]
                        item.pop(old_id)
                converted_data.append(item)
        except KeyError:
            breakpoint()
        return converted_data

    @staticmethod
    def get_import_sequence(models, dependencies):
        # Perform topological sorting to get the import sequence
        import_sequence = []
        visited = set()

        def dfs(model):
            if model not in visited:
                visited.add(model)
                for dependent_model in dependencies[model]:
                    dfs(dependent_model)
                import_sequence.append(model)

        for model in models:
            dfs(model)

        import_sequence.reverse()  # Reverse to get correct import sequence

        return import_sequence

    @staticmethod
    def prepare_update_on(row, table_update_on):
        update_criteria = {}
        # Split the filter string into key-value pairs
        update_pairs = table_update_on.split(',')
        # Iterate over each key-value pair and construct the filter criteria
        for pair in update_pairs:
            update_criteria[pair.strip()] = row.pop(pair.strip())
        return update_criteria, row

    @transaction.atomic
    def handle(self, *args, **options):
        bucket_name = "bucket-test"
        folder_name = ""
        folder_path = "/Users/ek055891/Warehouse/milkbasket/metadata/data_folder"

        download_folder_from_object_storage(bucket_name, folder_name, folder_path)

        # Fetch data from the database
        related_obj ={}
        start_time = datetime.now()
        models_to_export = LONMetadataSync.objects.filter(is_active=True)
        exported_models = []
        dependencies = {f'{m.app_name}.{m.model_name}': ast.literal_eval(m.dependency) for m in models_to_export}
        sorted_order = self.topological_sort(dependencies)
        self.stdout.write(f'Import Order: {sorted_order}')
        ordered_models_to_export = []
        for sorted_model in sorted_order:
            for model in models_to_export:
                if f'{model.app_name}.{model.model_name}' == sorted_model:
                    ordered_models_to_export.append(model)


        for app_model in ordered_models_to_export:
            related_obj[app_model.model_name] = {}
            app_label, model_name, report_name = app_model.app_name, app_model.model_name, app_model.report_name
            ModelClass = apps.get_model(app_label, model_name)
            if ModelClass is None:
                self.stdout.write(
                    self.style.ERROR(
                        f"Model '{app_model.app_name, app_model.model_name}' not found. Skipping."))
                continue
            print(f"Reading {app_model.app_name, app_model.model_name}...", end='',
                  flush=True)

            json_file = f'metadata/data_folder/{report_name}/{app_label}.{model_name}.json'
            # Prepare queryset
            with open(json_file, 'r') as file:
                json_data = json.load(file)

            converted_data = self.convert_data_types(json_data, related_obj)

            if app_model.full_refresh or app_model.table_update_on is None:
                # Create a list of YourModel objects
                self.clean_table(ModelClass, app_model)
                objects_to_create = [ModelClass(**item) for item in converted_data]
                try:
                    ModelClass.objects.bulk_create(objects_to_create)
                except:
                    raise ValueError
                #     pass
                print("UPDATED")

            else:
                # Update
                created_rows, updated_rows = 0, 0
                update_on = app_model.table_update_on

                for row in converted_data:
                    update_on_cols, default_data = self.prepare_update_on(row, update_on)
                    if app_model.seq_field:
                        old_id = default_data.pop(app_model.seq_field)
                    obj, created = ModelClass.objects.update_or_create(
                        **update_on_cols,
                        defaults=default_data,
                    )
                    if created:
                        created_rows += 1
                    else:
                        updated_rows += 1

                    if app_model.seq_field or len(json_data['required_by']):
                        related_obj[app_model.model_name][old_id] = obj

                self.stdout.write(
                    f"{app_label}.{model_name} - {created_rows} rows created, {updated_rows} rows updated")


        self.stdout.write(self.style.SUCCESS(f"Data imported successfully!"))
