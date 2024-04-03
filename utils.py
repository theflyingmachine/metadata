import json
import os
import sys

import oci
import subprocess
from datetime import datetime

from django.apps import apps
from django.db.models import ForeignKey, ManyToManyField, Q

from core.models import LonForeignKey
from lon import settings
from metadata.models import LONMetadataSync


class MetadataSync:

    def __init__(self):
        self.bucket_name = "LightsOn-Metadata-bucket"
        self.bucket_folder_location = f"lon-{settings.DEPLOYMENT_MODE}"
        self.local_data_dir = 'metadata/local_data'
        self.git_repo = GitRepo()
        self.object_storage = ObjectStore(self.bucket_name, self.local_data_dir)

    @staticmethod
    def topological_sort(dependencies, models_to_export):
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

        ordered_models_to_export = []
        for sorted_model in stack:
            for model in models_to_export:
                if f'{model.app_name}.{model.model_name}' == sorted_model:
                    ordered_models_to_export.append(model)

        return ordered_models_to_export

    @staticmethod
    def save_json(data, folder, file_name):
        file_path = os.path.join(folder, f'{file_name}.json')
        if not os.path.exists(folder):
            os.makedirs(folder)

        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    @staticmethod
    def custom_json_serializer(obj):
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [MetadataSync.custom_json_serializer(item) for item in obj]
        elif isinstance(obj, dict):
            return {str(key): MetadataSync.custom_json_serializer(value) for key, value in
                    obj.items()}
        return str(obj)

    @staticmethod
    def serialize_data(queryset, export_pref):
        if export_pref.exclude_columns:
            exclude_column_names = [item.strip() for item in
                                    export_pref.exclude_columns.split(',')]
            return [
                {key: MetadataSync.custom_json_serializer(value) for key, value in qs.items() if
                 key not in exclude_column_names} for qs in queryset] if queryset else []
        return [{key: MetadataSync.custom_json_serializer(value) for key, value in qs.items()} for
                qs in
                queryset] if queryset else []

    @staticmethod
    def prepare_queryset(model_class, export_pref):
        filters = json.loads(export_pref.table_filters) if export_pref.table_filters else {}
        queryset = model_class.objects.filter(**filters).values()

        if export_pref.ready_to_copy:
            model_class.objects.filter(**filters).update(ready_to_copy=False)
        return queryset

    @staticmethod
    def get_model_datatypes(model_class):
        column_data_types = {}
        dependent_models = []
        for field in model_class._meta.fields:
            column_data_types[field.name] = {'type': field.get_internal_type()}
            if field.get_internal_type() in (
                    'ForeignKey', 'LonForeignKey', 'ManyToManyField', 'OneToOneField'):
                related_model = field.related_model
                column_data_types[field.name]['related_model'] = related_model._meta.object_name
                column_data_types[field.name]['related_app'] = related_model._meta.app_label
                column_data_types[field.name]['field_name'] = field.attname
                dependent_models.append(
                    f'{related_model._meta.app_label}.{related_model._meta.object_name}')
        return column_data_types, list(set(dependent_models))

    @staticmethod
    def filter_related_data(queryset, parent_querysets):
        # Get the related filters for each parent_queryset
        parent_filters = Q()
        for parent_queryset, condition in parent_querysets:
            for field in queryset.model._meta.get_fields():
                if (isinstance(field, (ForeignKey, ManyToManyField, LonForeignKey))
                        and field.related_model == parent_queryset.model):
                    parent_ids = parent_queryset.values_list('pk', flat=True)
                    filter_kwargs = {f'{field.name}__in': parent_ids}
                    if condition == 'AND':
                        parent_filters &= Q(**filter_kwargs)
                    elif condition == 'OR':
                        parent_filters |= Q(**filter_kwargs)

        return queryset.filter(parent_filters)


class ExportMetadata(MetadataSync):
    def process(self, push_option):
        sys.stdout.write('Exporting metadata...\n')
        all_models = LONMetadataSync.objects.filter(is_active=True)
        dependencies, meta_tree = {}, {}
        for app_model in all_models:
            if not app_model.app_name and not app_model.model_name:
                continue
            try:
                model_class = apps.get_model(app_model.app_name, app_model.model_name)
            except LookupError:
                sys.stdout.write(
                    f"Model '{app_model.app_name, app_model.model_name}' not found. Skipping.\n")
                continue
            column_data_types, dependent_models = self.get_model_datatypes(model_class)
            meta_tree[f'{app_model.app_name}.{app_model.model_name}'] = {
                'dependency': sorted(dependent_models),
                'required_by': [],
                'metadata': column_data_types,
                'model': model_class,
                'app_model': app_model
            }

        dependency_map = {model_name: set(model_data["dependency"]) for model_name, model_data in
                          meta_tree.items()}

        for model_name, model_data in meta_tree.items():
            for dependency in model_data["dependency"]:
                if dependency in meta_tree:
                    meta_tree[dependency]["required_by"].append(model_name)

        models_to_export = self.topological_sort(dependency_map, all_models)
        model_qs_mapper = {}
        files_to_upload = []
        count, total = 0, len(models_to_export)
        self.git_repo.git_checkout()
        for model in models_to_export:
            count += 1
            current_model_app = f'{model.app_name}.{model.model_name}'
            sys.stdout.write(f'({count}/{total}) {current_model_app}...')
            json_data = meta_tree[current_model_app]
            model_class = json_data.pop('model')
            app_model = json_data.pop('app_model')
            queryset = self.prepare_queryset(model_class, app_model)

            # This model depends on something, get its parent queryset
            if json_data['dependency'] and model.inherit_parent_filter:
                inherit_filters = json.loads(model.inherit_parent_filter)
                parent_qs = [(model_qs_mapper[dep], condition) for dep, condition in
                             inherit_filters.items() if
                             dep in model_qs_mapper and dep != current_model_app]
                queryset = self.filter_related_data(queryset, parent_qs)

            # Store qs if model has any dependent model
            if json_data['required_by']:
                model_qs_mapper[current_model_app] = queryset

            json_data['data'] = self.serialize_data(queryset, model)

            folder = f'{self.local_data_dir}/{model.report_name}'
            self.save_json(json_data, folder, current_model_app)
            files_to_upload.append(f'{model.report_name}/{current_model_app}.json')

            sys.stdout.write('Done\n')
        if push_option in ('all', 'bucket'):
            sys.stdout.write('Pushing to Object Store...\n')
            for file in files_to_upload:
                self.object_storage.upload_files_to_object_storage(file,
                                                                   self.bucket_folder_location)
        if push_option in ('all', 'github'):
            sys.stdout.write('Pushing to Git...\n')
            self.git_repo.git_commit(files_to_upload)


class ObjectStore:
    def __init__(self, bucket_name, directory_path):
        config = {
            "user": "ocid1.user.oc1..aaaaaaaa6gt2deui2xbvww4us6damjazbswbpxsgqfay2me25uvysuutsgaq",
            "key_file": "/opt/lon/src/eric.kalloor@oracle.com_2024-03-20T18_02_33.544Z.pem",
            "fingerprint": "c1:74:3d:f3:b5:40:9f:9c:44:4f:b6:82:86:03:76:bb",
            "tenancy": "ocid1.tenancy.oc1..aaaaaaaavx7he3elr6uirjtqbsaazgs6rkuoopn4ogyqglyfqkkiv53steva",
            "region": "ap-mumbai-1",
            "compartment_id": "ocid1.compartment.oc1..aaaaaaaamvaga6h7ttqtan7xnbpa4qem7sxahxfmrjz4wuhvryft5z5dcuja"
        }
        self.namespace_name = 'bml6yrcway4k'
        self.bucket_name = bucket_name
        self.directory_path = directory_path
        self.object_storage = oci.object_storage.ObjectStorageClient(config)

    def upload_files_to_object_storage(self, item, parent_folder=''):
        item_path = os.path.join(self.directory_path, item)
        object_name = os.path.join(parent_folder, item) if parent_folder else item
        with open(item_path, 'rb') as file:
            self.object_storage.put_object(self.namespace_name, self.bucket_name, object_name,
                                           file)
        sys.stdout.write(f"Uploaded {object_name}\n")


class GitRepo:
    def __init__(self):
        self.repo_path = 'metadata/local_data'  # Path to your repository directory
        self.commit_message = f'Exported on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        self.remote_url = f'https://{settings.GIT_METADATA_PAT}@github.cerner.com/EK055891/LightsOn_Site_Metadata.git'
        self.branch_name = f'lon-{settings.DEPLOYMENT_MODE}'

        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

    def run_git_command(self, command: list, raise_exception: bool = True):
        result = subprocess.run(command, cwd=self.repo_path, capture_output=True, text=True)
        if raise_exception and result.returncode:
            raise Exception(result)
        sys.stdout.write(result.stdout)
        return result

    def git_init(self):
        if not os.path.exists(os.path.join(self.repo_path, '.git')):
            self.run_git_command(['git', 'init'])
            self.run_git_command(['git', 'remote', 'add', 'origin', self.remote_url])

    def git_checkout(self):
        self.git_init()
        result = self.run_git_command(['git', 'checkout', self.branch_name], raise_exception=False)
        git_checkout = ['git', 'checkout', '-b', self.branch_name] if result.returncode else \
            ['git', 'reset', '--hard', 'HEAD']
        self.run_git_command(git_checkout)
        self.run_git_command(['git', 'pull', 'origin', self.branch_name])

    def git_commit(self, files_to_upload):
        for file in files_to_upload:
            self.run_git_command(['git', 'add', file])

        self.run_git_command(['git', 'commit', '-m', self.commit_message], raise_exception=False)
        self.run_git_command(['git', 'push', 'origin', self.branch_name])
